from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.parking_spot import ParkingSpot


class ParkingSpotRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, spot_id: int) -> ParkingSpot | None:
        return self.db.get(ParkingSpot, spot_id)

    def list_for_parking(self, parking_id: int) -> list[ParkingSpot]:
        return list(
            self.db.scalars(
                select(ParkingSpot)
                .where(ParkingSpot.parking_id == parking_id)
                .order_by(ParkingSpot.code)
            ).all()
        )

    def create(self, **kwargs) -> ParkingSpot:
        spot = ParkingSpot(**kwargs)
        self.db.add(spot)
        self.db.flush()
        return spot
