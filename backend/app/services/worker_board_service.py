from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking
from app.models.enums import BookingStatus, SessionStatus, SpotStatus
from app.models.parking_session import ParkingSession
from app.models.parking_spot import ParkingSpot
from app.schemas.booking import BookingWithPaymentsRead
from app.schemas.session import ParkingSessionRead
from app.schemas.spot import ParkingSpotRead
from app.schemas.vehicle import VehicleRead
from app.schemas.worker_board import WorkerSpotBoardItem
from app.services.util import as_utc


def list_parking_spot_board(db: Session, *, parking_id: int) -> list[WorkerSpotBoardItem]:
    spots = db.scalars(
        select(ParkingSpot).where(ParkingSpot.parking_id == parking_id).order_by(ParkingSpot.code)
    ).all()
    now = datetime.now(timezone.utc)
    out: list[WorkerSpotBoardItem] = []

    for spot in spots:
        vehicle = None
        booking_read: BookingWithPaymentsRead | None = None
        session_read: ParkingSessionRead | None = None
        overstay: int | None = None

        if spot.status == SpotStatus.inactive:
            out.append(
                WorkerSpotBoardItem(
                    spot=ParkingSpotRead.model_validate(spot),
                    vehicle=None,
                    booking=None,
                    session=None,
                    overstay_minutes=None,
                )
            )
            continue

        if spot.status == SpotStatus.occupied:
            sess = db.scalars(
                select(ParkingSession)
                .join(Booking, Booking.id == ParkingSession.booking_id)
                .where(
                    Booking.spot_id == spot.id,
                    Booking.parking_id == parking_id,
                    ParkingSession.status == SessionStatus.active,
                )
                .options(
                    joinedload(ParkingSession.booking).joinedload(Booking.vehicle),
                    joinedload(ParkingSession.booking).joinedload(Booking.payments),
                    joinedload(ParkingSession.booking).joinedload(Booking.tariff),
                )
            ).first()
            if sess:
                booking = sess.booking
                vehicle = booking.vehicle
                booking_read = BookingWithPaymentsRead.model_validate(booking, from_attributes=True)
                session_read = ParkingSessionRead.model_validate(sess, from_attributes=True)
                end_utc = as_utc(booking.planned_end_time)
                if now > end_utc:
                    overstay = int((now - end_utc).total_seconds() // 60)
        elif spot.status == SpotStatus.reserved:
            booking = db.scalars(
                select(Booking)
                .where(
                    Booking.spot_id == spot.id,
                    Booking.parking_id == parking_id,
                    Booking.status.in_((BookingStatus.created, BookingStatus.paid)),
                )
                .options(
                    joinedload(Booking.vehicle),
                    joinedload(Booking.payments),
                    joinedload(Booking.tariff),
                )
                .order_by(Booking.created_at.desc())
            ).first()
            if booking:
                vehicle = booking.vehicle
                booking_read = BookingWithPaymentsRead.model_validate(booking, from_attributes=True)

        out.append(
            WorkerSpotBoardItem(
                spot=ParkingSpotRead.model_validate(spot),
                vehicle=VehicleRead.model_validate(vehicle, from_attributes=True) if vehicle else None,
                booking=booking_read,
                session=session_read,
                overstay_minutes=overstay,
            )
        )

    return out
