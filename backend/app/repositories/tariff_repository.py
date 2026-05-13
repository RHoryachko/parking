from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tariff import Tariff


class TariffRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, tariff_id: int) -> Tariff | None:
        return self.db.get(Tariff, tariff_id)

    def list_for_parking(self, parking_id: int) -> list[Tariff]:
        return list(self.db.scalars(select(Tariff).where(Tariff.parking_id == parking_id)).all())

    def create(self, **kwargs) -> Tariff:
        tariff = Tariff(**kwargs)
        self.db.add(tariff)
        self.db.flush()
        return tariff
