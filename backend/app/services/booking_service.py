import base64
import json
import logging
import math
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, liqpay_keys
from app.models.booking import Booking
from app.models.enums import BookingStatus, PaymentStatus, SessionStatus, SpotStatus, UserRole
from app.models.payment import Payment
from app.models.parking_session import ParkingSession
from app.models.parking_spot import ParkingSpot
from app.models.tariff import Tariff
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services.liqpay_client import request_checkout_redirect_url, verify_callback_signature

logger = logging.getLogger(__name__)


def _assert_no_overlapping_booking_window(
    db: Session,
    *,
    user_id: int,
    planned_start_time: datetime,
    planned_end_time: datetime,
    exclude_booking_id: int | None = None,
) -> None:
    """At most one active reservation window (created/paid) per user for overlapping times."""
    conds = [
        Booking.user_id == user_id,
        Booking.status.in_((BookingStatus.created, BookingStatus.paid)),
        Booking.planned_start_time < planned_end_time,
        Booking.planned_end_time > planned_start_time,
    ]
    if exclude_booking_id is not None:
        conds.append(Booking.id != exclude_booking_id)
    if db.scalar(select(Booking.id).where(and_(*conds)).limit(1)) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "You already have a booking or paid reservation that overlaps this time range",
        )


def liqpay_result_url(cfg: Settings, booking_id: int) -> str:
    """LiqPay result_url: LIQPAY_RESULT_URL, else Flutter /payment-success?booking_id=…, else API /payment/success."""
    base = (cfg.LIQPAY_RESULT_URL or "").strip()
    if not base:
        client = (cfg.CLIENT_APP_WEB_URL or "").strip()
        if client:
            # Dedicated route (see flutter main.dart); avoids edge cases with query-only on `/`.
            base = f"{client.rstrip('/')}/payment-success"
        else:
            base = f"{cfg.APP_PUBLIC_API_URL.rstrip('/')}/payment/success"
    parts = urlsplit(base)
    q = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "booking_id"]
    q.append(("booking_id", str(booking_id)))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


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

    if planned_end_time <= planned_start_time:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "planned_end_time must be after planned_start_time")

    _assert_no_overlapping_booking_window(
        db,
        user_id=user.id,
        planned_start_time=planned_start_time,
        planned_end_time=planned_end_time,
    )

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


def create_booking_for_client(
    db: Session,
    *,
    client_user_id: int,
    vehicle_id: int,
    parking_id: int,
    spot_id: int,
    tariff_id: int,
    planned_start_time: datetime,
    planned_end_time: datetime,
) -> Booking:
    """Same rules as client self-service booking, but the worker picks the client account."""
    owner = db.get(User, client_user_id)
    if not owner or owner.role != UserRole.client:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "user_id must be a client account")

    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != owner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")

    spot = db.get(ParkingSpot, spot_id)
    if not spot or spot.parking_id != parking_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Spot does not belong to parking")
    if spot.status != SpotStatus.free:
        raise HTTPException(status.HTTP_409_CONFLICT, "Spot is not free")

    tariff = db.get(Tariff, tariff_id)
    if not tariff or tariff.parking_id != parking_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tariff does not belong to parking")

    if planned_end_time <= planned_start_time:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "planned_end_time must be after planned_start_time")

    _assert_no_overlapping_booking_window(
        db,
        user_id=owner.id,
        planned_start_time=planned_start_time,
        planned_end_time=planned_end_time,
    )

    booking = Booking(
        user_id=owner.id,
        vehicle_id=vehicle_id,
        parking_id=parking_id,
        spot_id=spot_id,
        tariff_id=tariff_id,
        planned_start_time=planned_start_time,
        planned_end_time=planned_end_time,
        status=BookingStatus.created,
    )
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

    active_sess = db.scalar(
        select(ParkingSession.id).where(
            ParkingSession.booking_id == booking.id,
            ParkingSession.status == SessionStatus.active,
        )
    )
    if active_sess is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Cannot cancel: this booking has an active parking session",
        )

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

    for p in db.scalars(
        select(Payment).where(
            Payment.booking_id == booking.id,
            Payment.status == PaymentStatus.pending,
        )
    ).all():
        p.status = PaymentStatus.failed

    _assert_no_overlapping_booking_window(
        db,
        user_id=user.id,
        planned_start_time=booking.planned_start_time,
        planned_end_time=booking.planned_end_time,
        exclude_booking_id=booking.id,
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


def pay_booking_worker_mock(db: Session, *, worker_id: int, booking_id: int) -> Booking:
    """Cashier / terminal: mark a client's unpaid booking as paid (same as mock client pay)."""
    from app.services import worker_service

    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    worker_service.ensure_worker_parking(db, worker_id, booking.parking_id)
    if booking.status != BookingStatus.created:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Only bookings in 'created' can be paid",
        )

    # Cashier confirms payment in person: supersede any unfinished LiqPay checkout row (no gateway check).
    for p in db.scalars(
        select(Payment).where(
            Payment.booking_id == booking.id,
            Payment.status == PaymentStatus.pending,
        )
    ).all():
        p.status = PaymentStatus.failed

    _assert_no_overlapping_booking_window(
        db,
        user_id=booking.user_id,
        planned_start_time=booking.planned_start_time,
        planned_end_time=booking.planned_end_time,
        exclude_booking_id=booking.id,
    )

    hours = _planned_billable_hours(booking)
    amount = (booking.tariff.price_per_hour * hours).quantize(Decimal("0.01"))
    now = datetime.now(timezone.utc)

    payment = Payment(
        booking_id=booking.id,
        session_id=None,
        user_id=booking.user_id,
        amount=amount,
        status=PaymentStatus.paid,
        paid_at=now,
    )
    db.add(payment)
    booking.status = BookingStatus.paid
    db.flush()
    return booking


def start_liqpay_checkout(db: Session, *, user: User, booking_id: int) -> tuple[str, int]:
    """Creates a pending payment and returns (checkout_url, payment_id). Requires LiqPay keys."""
    cfg = Settings()
    pub, priv = liqpay_keys()
    if not pub or not priv:
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

    server_url = f"{cfg.APP_PUBLIC_API_URL.rstrip('/')}/api/payments/liqpay/callback"
    description = f"Parking booking #{booking.id}"

    host = urlsplit(server_url).hostname or ""
    if host in ("127.0.0.1", "localhost"):
        logger.warning(
            "LiqPay server_url uses %s — LiqPay cannot call your API from the internet. "
            "Use ngrok/cloudflared (or deploy) and set APP_PUBLIC_API_URL to the public HTTPS URL, "
            "otherwise the card step often ends with a generic transaction error.",
            host,
        )

    try:
        url = request_checkout_redirect_url(
            public_key=pub,
            private_key=priv,
            amount=amount,
            order_id=order_id,
            description=description,
            server_url=server_url,
            result_url=liqpay_result_url(cfg, booking.id),
        )
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    db.flush()
    return url, payment.id


def apply_liqpay_callback(*, db: Session, data_b64: str, signature: str) -> dict:
    """Verify LiqPay server callback and mark booking paid on success."""
    pub, priv = liqpay_keys()
    if not priv or not pub:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "LiqPay not configured")

    if not verify_callback_signature(
        private_key=priv,
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
    if payment.status == PaymentStatus.failed:
        # e.g. abandoned LiqPay attempt after cashier pay, or gateway failure — do not resurrect this row
        return {"status": "ok", "detail": "payment_inactive"}

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

    _assert_no_overlapping_booking_window(
        db,
        user_id=booking.user_id,
        planned_start_time=booking.planned_start_time,
        planned_end_time=booking.planned_end_time,
        exclude_booking_id=booking.id,
    )

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

    if planned_end_time <= planned_start_time:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "planned_end_time must be after planned_start_time")

    _assert_no_overlapping_booking_window(
        db,
        user_id=client_user_id,
        planned_start_time=planned_start_time,
        planned_end_time=planned_end_time,
    )

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
