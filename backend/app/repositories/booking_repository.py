from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, booking_id: int) -> Booking | None:
        return self.db.get(Booking, booking_id)

    def list_for_user(self, user_id: int) -> list[Booking]:
        return list(
            self.db.scalars(
                select(Booking)
                .where(Booking.user_id == user_id)
                .order_by(Booking.created_at.desc())
            ).all()
        )

    def latest_by_vehicle_and_parking(self, vehicle_id: int, parking_id: int) -> Booking | None:
        return self.db.scalars(
            select(Booking)
            .where(Booking.vehicle_id == vehicle_id, Booking.parking_id == parking_id)
            .options(joinedload(Booking.payments))
            .order_by(Booking.created_at.desc())
            .limit(1)
        ).first()

    def create(self, **kwargs) -> Booking:
        booking = Booking(**kwargs)
        self.db.add(booking)
        self.db.flush()
        return booking
