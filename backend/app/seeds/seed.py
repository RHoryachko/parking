"""
Idempotent seed data for local/demo.

Run from `backend/` after migrations:
    python -m app.seeds.seed
"""

from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import SpotStatus, UserRole, WorkMode
from app.models.parking import Parking
from app.models.parking_spot import ParkingSpot
from app.models.tariff import Tariff
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.worker_assignment import WorkerAssignment
from app.services.util import normalize_plate


def run() -> None:
    db = SessionLocal()
    try:
        def ensure_user(email: str, **kwargs) -> User:
            u = db.scalar(select(User).where(User.email == email))
            if u:
                return u
            u = User(email=email, **kwargs)
            db.add(u)
            db.flush()
            return u

        admin = ensure_user(
            "admin@parking.local",
            full_name="Admin User",
            phone=None,
            password_hash=hash_password("admin123"),
            role=UserRole.admin,
            is_blocked=False,
        )
        worker = ensure_user(
            "worker@parking.local",
            full_name="Worker User",
            phone=None,
            password_hash=hash_password("worker123"),
            role=UserRole.worker,
            is_blocked=False,
        )
        client = ensure_user(
            "client@parking.local",
            full_name="Client User",
            phone="+380501112233",
            password_hash=hash_password("client123"),
            role=UserRole.client,
            is_blocked=False,
        )
        _ = admin, client  # referenced for clarity / future extension

        parking = db.scalar(select(Parking).where(Parking.name == "Central Lot"))
        if not parking:
            parking = Parking(
                name="Central Lot",
                city="Kyiv",
                address="vul. Khreshchatyk 1",
                capacity=10,
                latitude=50.4501,
                longitude=30.5234,
                work_mode=WorkMode.manual,
            )
            db.add(parking)
            db.flush()

        if not db.scalars(select(ParkingSpot).where(ParkingSpot.parking_id == parking.id)).first():
            for i in range(1, 11):
                db.add(
                    ParkingSpot(
                        parking_id=parking.id,
                        code=f"A{i}",
                        status=SpotStatus.free,
                    )
                )

        if not db.scalars(select(Tariff).where(Tariff.parking_id == parking.id)).first():
            db.add(Tariff(parking_id=parking.id, price_per_hour=Decimal("50.00")))

        parking2 = db.scalar(select(Parking).where(Parking.name == "Podil Riverside"))
        if not parking2:
            parking2 = Parking(
                name="Podil Riverside",
                city="Kyiv",
                address="Naberezhne shose 7",
                capacity=5,
                latitude=50.4715,
                longitude=30.5178,
                work_mode=WorkMode.manual,
            )
            db.add(parking2)
            db.flush()
            for i in range(1, 6):
                db.add(
                    ParkingSpot(
                        parking_id=parking2.id,
                        code=f"B{i}",
                        status=SpotStatus.free,
                    )
                )
            db.add(Tariff(parking_id=parking2.id, price_per_hour=Decimal("40.00")))

        if not db.scalar(
            select(WorkerAssignment.id).where(
                WorkerAssignment.worker_id == worker.id,
                WorkerAssignment.parking_id == parking.id,
            )
        ):
            db.add(WorkerAssignment(worker_id=worker.id, parking_id=parking.id))

        plate = normalize_plate("AA1234BC")
        if not db.scalar(select(Vehicle.id).where(Vehicle.plate_number == plate)):
            db.add(
                Vehicle(
                    user_id=client.id,
                    plate_number=plate,
                    brand="Toyota",
                    model="Camry",
                    color="Silver",
                )
            )

        db.commit()
        print("Seed completed: admin@parking.local / worker@parking.local / client@parking.local")
    finally:
        db.close()


if __name__ == "__main__":
    run()
