from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import WorkMode


class Parking(Base):
    __tablename__ = "parkings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    work_mode: Mapped[WorkMode] = mapped_column(
        Enum(WorkMode, name="workmode"), nullable=False, default=WorkMode.manual
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    spots = relationship("ParkingSpot", back_populates="parking", cascade="all, delete-orphan")
    tariffs = relationship("Tariff", back_populates="parking", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="parking")
    worker_assignments = relationship("WorkerAssignment", back_populates="parking")
    barrier_logs = relationship("BarrierLog", back_populates="parking")
    ai_logs = relationship("AiLog", back_populates="parking")
