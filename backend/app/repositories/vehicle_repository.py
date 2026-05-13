from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle


class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, vehicle_id: int) -> Vehicle | None:
        return self.db.get(Vehicle, vehicle_id)

    def find_by_plate(self, plate_number: str) -> Vehicle | None:
        return self.db.scalar(select(Vehicle).where(Vehicle.plate_number == plate_number))

    def list_by_user(self, user_id: int) -> list[Vehicle]:
        return list(self.db.scalars(select(Vehicle).where(Vehicle.user_id == user_id)).all())

    def create(self, **kwargs) -> Vehicle:
        vehicle = Vehicle(**kwargs)
        self.db.add(vehicle)
        self.db.flush()
        return vehicle
