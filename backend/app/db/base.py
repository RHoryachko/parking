from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so Alembic sees metadata
from app.models import (  # noqa: E402, F401
    ai_log,
    barrier_log,
    booking,
    payment,
    parking,
    parking_session,
    parking_spot,
    tariff,
    user,
    vehicle,
    worker_assignment,
)
