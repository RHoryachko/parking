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
from app.services.util import as_utc, normalize_plate


def _billing_hours(entry: datetime, exit_at: datetime) -> int:
    a = as_utc(entry)
    b = as_utc(exit_at)
    secs = (b - a).total_seconds()
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
    db: Session,
    *,
    parking_id: int,
    plate: str,
    require_inside_planned_window: bool = True,
) -> Booking | None:
    """Find a paid booking for this parking + plate; spot still reserved; optional planned-time window."""
    norm = normalize_plate(plate)
    conds = [
        Booking.parking_id == parking_id,
        Booking.status == BookingStatus.paid,
        Vehicle.plate_number == norm,
    ]
    if require_inside_planned_window:
        now = datetime.now(timezone.utc)
        conds.append(Booking.planned_start_time <= now)
        conds.append(Booking.planned_end_time >= now)
    stmt = (
        select(Booking)
        .join(Vehicle, Vehicle.id == Booking.vehicle_id)
        .where(*conds)
        .options(joinedload(Booking.spot), joinedload(Booking.tariff), joinedload(Booking.session))
        .order_by(Booking.created_at.desc())
    )
    for booking in db.scalars(stmt).unique().all():
        if booking.session is not None:
            continue
        if booking.spot and booking.spot.status == SpotStatus.reserved:
            return booking
    return None


def _finalize_entry_from_booking(db: Session, booking: Booking) -> ParkingSession:
    """Create active session from a paid booking (worker / AI gate flow)."""
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


def register_entry(
    db: Session,
    *,
    parking_id: int,
    plate_number: str,
    require_inside_planned_window: bool = False,
) -> ParkingSession:
    """
    Car enters: paid booking + reserved spot -> create active session, booking used, spot occupied.

    Workers may register entry outside the client's planned window (early/late arrival).
    Automated flows (AI) should pass require_inside_planned_window=True.
    """
    booking = find_paid_booking_for_entry(
        db,
        parking_id=parking_id,
        plate=plate_number,
        require_inside_planned_window=require_inside_planned_window,
    )
    if not booking:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No paid booking with reserved spot for this plate and parking",
        )
    return _finalize_entry_from_booking(db, booking)


def find_active_session_by_parking_plate(
    db: Session, *, parking_id: int, plate: str
) -> ParkingSession | None:
    """Active session on this parking for vehicle with normalized plate (newest if multiple)."""
    norm = normalize_plate(plate)
    stmt = (
        select(ParkingSession)
        .join(Booking, Booking.id == ParkingSession.booking_id)
        .join(Vehicle, Vehicle.id == Booking.vehicle_id)
        .where(
            ParkingSession.status == SessionStatus.active,
            Booking.parking_id == parking_id,
            Vehicle.plate_number == norm,
        )
        .order_by(ParkingSession.entry_time.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


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
