from sqlalchemy import distinct, select
from sqlalchemy.orm import Session, selectinload

from app.models.parking import Parking


class ParkingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, parking_id: int) -> Parking | None:
        return self.db.get(Parking, parking_id)

    def get_with_tariffs(self, parking_id: int) -> Parking | None:
        return self.db.scalars(
            select(Parking)
            .where(Parking.id == parking_id)
            .options(selectinload(Parking.tariffs))
        ).first()

    def list_parkings(self, city: str | None = None) -> list[Parking]:
        stmt = select(Parking).order_by(Parking.name)
        if city:
            stmt = stmt.where(Parking.city == city)
        return list(self.db.scalars(stmt).all())

    def list_cities(self) -> list[str]:
        return list(self.db.scalars(select(distinct(Parking.city)).order_by(Parking.city)).all())

    def create(self, **kwargs) -> Parking:
        parking = Parking(**kwargs)
        self.db.add(parking)
        self.db.flush()
        return parking
