import base64
import json
import logging
import math
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.booking import Booking
from app.models.enums import BookingStatus, PaymentStatus, SpotStatus, UserRole
from app.models.payment import Payment
from app.models.parking_spot import ParkingSpot
from app.models.tariff import Tariff
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services.liqpay_client import request_checkout_redirect_url, verify_callback_signature

logger = logging.getLogger(__name__)


def _planned_billable_hours(booking: Booking) -> int:
    secs = (booking.planned_end_time - booking.planned_start_time).total_seconds()
    return max(1, math.ceil(secs / 3600))


def create_booking(
    db: Session,
    *,
    user: User,
    vehicle_id: int,
    parking_id: int,
    spot_id: int,
    tariff_id: int,
    planned_start_time: datetime,
    planned_end_time: datetime,
) -> Booking:
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")

    spot = db.get(ParkingSpot, spot_id)
    if not spot or spot.parking_id != parking_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Spot does not belong to parking")
    if spot.status != SpotStatus.free:
        raise HTTPException(status.HTTP_409_CONFLICT, "Spot is not free")

    tariff = db.get(Tariff, tariff_id)
    if not tariff or tariff.parking_id != parking_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tariff does not belong to parking")

    booking = Booking(
        user_id=user.id,
        vehicle_id=vehicle_id,
        parking_id=parking_id,
        spot_id=spot_id,
        tariff_id=tariff_id,
        planned_start_time=planned_start_time,
        planned_end_time=planned_end_time,
        status=BookingStatus.created,
    )
    # Reserve spot when booking is created
    spot.status = SpotStatus.reserved
    db.add(booking)
    db.flush()
    return booking


def cancel_booking(db: Session, *, user: User, booking_id: int, is_admin: bool = False) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if not is_admin and booking.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your booking")
    if booking.status in (BookingStatus.canceled, BookingStatus.used):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Booking cannot be canceled")
    if booking.status == BookingStatus.expired:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Booking is expired")

    spot = booking.spot
    # Release reservation if still tied to this unpaid/paid-but-not-entered flow
    if spot and spot.id == booking.spot_id and spot.status == SpotStatus.reserved:
        spot.status = SpotStatus.free

    pending = db.scalars(
        select(Payment).where(Payment.booking_id == booking.id, Payment.status == PaymentStatus.pending)
    ).all()
    for pay in pending:
        pay.status = PaymentStatus.failed

    booking.status = BookingStatus.canceled
    db.flush()
    return booking


def pay_booking_mock(db: Session, *, user: User, booking_id: int) -> Booking:
    """Mock payment: marks booking paid and records a successful payment row."""
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your booking")
    if booking.status != BookingStatus.created:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Only bookings in 'created' can be paid"
        )

    pending = db.scalar(
        select(Payment.id).where(
            Payment.booking_id == booking.id,
            Payment.status == PaymentStatus.pending,
        )
    )
    if pending is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Complete or cancel the LiqPay checkout before using instant pay",
        )

    hours = _planned_billable_hours(booking)
    amount = (booking.tariff.price_per_hour * hours).quantize(Decimal("0.01"))
    now = datetime.now(timezone.utc)

    payment = Payment(
        booking_id=booking.id,
        session_id=None,
        user_id=user.id,
        amount=amount,
        status=PaymentStatus.paid,
        paid_at=now,
    )
    db.add(payment)
    booking.status = BookingStatus.paid
    # Spot stays reserved until entry or cancel
    db.flush()
    return booking


def start_liqpay_checkout(db: Session, *, user: User, booking_id: int) -> tuple[str, int]:
    """Creates a pending payment and returns (checkout_url, payment_id). Requires LiqPay keys."""
    if not settings.LIQPAY_PUBLIC_KEY or not settings.LIQPAY_PRIVATE_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "LiqPay is not configured (set LIQPAY_PUBLIC_KEY and LIQPAY_PRIVATE_KEY)",
        )

    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your booking")
    if booking.status != BookingStatus.created:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Only bookings in 'created' can be paid via LiqPay"
        )

    existing = db.scalar(
        select(Payment.id).where(
            Payment.booking_id == booking.id,
            Payment.status == PaymentStatus.pending,
        )
    )
    if existing is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "A LiqPay checkout is already in progress for this booking. Complete or cancel the booking.",
        )

    hours = _planned_billable_hours(booking)
    amount = (booking.tariff.price_per_hour * hours).quantize(Decimal("0.01"))
    payment = Payment(
        booking_id=booking.id,
        session_id=None,
        user_id=user.id,
        amount=amount,
        status=PaymentStatus.pending,
        paid_at=None,
    )
    db.add(payment)
    db.flush()
    order_id = str(payment.id)
    payment.liqpay_order_id = order_id

    server_url = f"{settings.APP_PUBLIC_API_URL.rstrip('/')}/api/payments/liqpay/callback"
    description = f"Parking booking #{booking.id}"

    try:
        url = request_checkout_redirect_url(
            public_key=settings.LIQPAY_PUBLIC_KEY,
            private_key=settings.LIQPAY_PRIVATE_KEY,
            amount=amount,
            order_id=order_id,
            description=description,
            server_url=server_url,
            result_url=settings.LIQPAY_RESULT_URL,
        )
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    db.flush()
    return url, payment.id


def apply_liqpay_callback(*, db: Session, data_b64: str, signature: str) -> dict:
    """Verify LiqPay server callback and mark booking paid on success."""
    if not settings.LIQPAY_PRIVATE_KEY or not settings.LIQPAY_PUBLIC_KEY:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "LiqPay not configured")

    if not verify_callback_signature(
        private_key=settings.LIQPAY_PRIVATE_KEY,
        data_b64=data_b64,
        signature=signature,
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid signature")

    try:
        payload = json.loads(base64.b64decode(data_b64).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid data") from exc

    order_id = str(payload.get("order_id", ""))
    if not order_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing order_id")

    payment = db.scalar(select(Payment).where(Payment.liqpay_order_id == order_id))
    if not payment or payment.booking_id is None:
        logger.warning("LiqPay callback for unknown order_id=%s", order_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")

    if payment.status == PaymentStatus.paid:
        return {"status": "ok", "detail": "already_paid"}

    liq_status = str(payload.get("status", ""))
    if liq_status != "success":
        payment.status = PaymentStatus.failed
        db.commit()
        return {"status": "ok", "detail": f"payment_{liq_status}"}

    try:
        cb_amount = Decimal(str(payload.get("amount", "0")))
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid amount in callback")

    if cb_amount.quantize(Decimal("0.01")) != payment.amount.quantize(Decimal("0.01")):
        logger.error(
            "LiqPay amount mismatch booking=%s payment=%s expected=%s got=%s",
            payment.booking_id,
            payment.id,
            payment.amount,
            cb_amount,
        )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Amount mismatch")

    booking = db.get(Booking, payment.booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking missing")

    if booking.status != BookingStatus.created:
        return {"status": "ok", "detail": "booking_not_payable"}

    now = datetime.now(timezone.utc)
    payment.status = PaymentStatus.paid
    payment.paid_at = now
    booking.status = BookingStatus.paid
    db.commit()
    return {"status": "ok"}


def create_manual_paid_booking(
    db: Session,
    *,
    vehicle_id: int,
    parking_id: int,
    spot_id: int,
    tariff_id: int,
    planned_start_time: datetime,
    planned_end_time: datetime,
    client_user_id: int,
) -> Booking:
    """
    Worker walk-in: booking starts as paid + spot reserved (same as create + pay).
    client_user_id is the vehicle owner's user id.
    """
    owner = db.get(User, client_user_id)
    if not owner or owner.role != UserRole.client:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "user_id must be a client account")

    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    if vehicle.user_id != client_user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vehicle does not belong to client")

    spot = db.get(ParkingSpot, spot_id)
    if not spot or spot.parking_id != parking_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Spot does not belong to parking")
    if spot.status != SpotStatus.free:
        raise HTTPException(status.HTTP_409_CONFLICT, "Spot is not free")

    tariff = db.get(Tariff, tariff_id)
    if not tariff or tariff.parking_id != parking_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tariff does not belong to parking")

    booking = Booking(
        user_id=client_user_id,
        vehicle_id=vehicle_id,
        parking_id=parking_id,
        spot_id=spot_id,
        tariff_id=tariff_id,
        planned_start_time=planned_start_time,
        planned_end_time=planned_end_time,
        status=BookingStatus.paid,
    )
    spot.status = SpotStatus.reserved
    db.add(booking)
    db.flush()

    hours = _planned_billable_hours(booking)
    amount = (tariff.price_per_hour * hours).quantize(Decimal("0.01"))
    now = datetime.now(timezone.utc)
    payment = Payment(
        booking_id=booking.id,
        session_id=None,
        user_id=client_user_id,
        amount=amount,
        status=PaymentStatus.paid,
        paid_at=now,
    )
    db.add(payment)
    db.flush()
    return booking
