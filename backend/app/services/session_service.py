import math
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking
from app.models.enums import BookingStatus, SessionStatus, SpotStatus
from app.models.parking_session import ParkingSession
from app.models.vehicle import Vehicle
from app.services.util import normalize_plate


def _billing_hours(entry: datetime, exit_at: datetime) -> int:
    secs = (exit_at - entry).total_seconds()
    return max(1, math.ceil(secs / 3600))


def user_has_active_parking_session(db: Session, user_id: int) -> bool:
    """True if this user already has an open (active) parking session on any booking."""
    stmt = (
        select(ParkingSession.id)
        .join(Booking, Booking.id == ParkingSession.booking_id)
        .where(Booking.user_id == user_id, ParkingSession.status == SessionStatus.active)
        .limit(1)
    )
    return db.scalar(stmt) is not None


def find_paid_booking_for_entry(
    db: Session, *, parking_id: int, plate: str
) -> Booking | None:
    """Find a paid booking for this parking + plate, within planned window, spot still reserved."""
    norm = normalize_plate(plate)
    now = datetime.now(timezone.utc)
    stmt = (
        select(Booking)
        .join(Vehicle, Vehicle.id == Booking.vehicle_id)
        .options(joinedload(Booking.spot), joinedload(Booking.tariff), joinedload(Booking.session))
        .where(
            Booking.parking_id == parking_id,
            Booking.status == BookingStatus.paid,
            Vehicle.plate_number == norm,
            Booking.planned_start_time <= now,
            Booking.planned_end_time >= now,
        )
        .order_by(Booking.created_at.desc())
    )
    for booking in db.scalars(stmt).unique().all():
        if booking.session is not None:
            continue
        if booking.spot and booking.spot.status == SpotStatus.reserved:
            return booking
    return None


def register_entry(db: Session, *, parking_id: int, plate_number: str) -> ParkingSession:
    """
    Car enters: paid booking + reserved spot -> create active session, booking used, spot occupied.
    """
    booking = find_paid_booking_for_entry(db, parking_id=parking_id, plate=plate_number)
    if not booking:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No paid booking with reserved spot for this plate and parking",
        )
    if booking.session:
        raise HTTPException(status.HTTP_409_CONFLICT, "Session already exists for this booking")
    if user_has_active_parking_session(db, booking.user_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This user already has an active parking session. Complete exit before a new entry.",
        )

    now = datetime.now(timezone.utc)
    parking_session = ParkingSession(
        booking_id=booking.id, entry_time=now, status=SessionStatus.active
    )
    booking.status = BookingStatus.used
    booking.spot.status = SpotStatus.occupied
    db.add(parking_session)
    db.flush()
    return parking_session


def register_exit(db: Session, *, session_id: int) -> ParkingSession:
    """Car exits: complete session, compute price from actual stay, free the spot."""
    session = db.get(ParkingSession, session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if session.status != SessionStatus.active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Session is not active")

    now = datetime.now(timezone.utc)
    booking = session.booking
    hours = _billing_hours(session.entry_time, now)
    price = (booking.tariff.price_per_hour * hours).quantize(Decimal("0.01"))

    session.exit_time = now
    session.total_price = price
    session.status = SessionStatus.completed
    booking.spot.status = SpotStatus.free
    db.flush()
    return session


def correct_session(
    db: Session,
    *,
    session_id: int,
    new_status: SessionStatus | None = None,
    exit_time: datetime | None = None,
    total_price: Decimal | None = None,
) -> ParkingSession:
    """Allow worker/admin to fix session row (e.g. wrong exit time)."""
    session = db.get(ParkingSession, session_id)
    if not session:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    if new_status is not None:
        session.status = new_status
    if exit_time is not None:
        session.exit_time = exit_time
    if total_price is not None:
        session.total_price = total_price
    db.flush()
    return session
