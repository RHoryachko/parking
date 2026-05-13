from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import BookingStatus


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    parking_id: Mapped[int] = mapped_column(
        ForeignKey("parkings.id", ondelete="RESTRICT"), nullable=False
    )
    spot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_spots.id", ondelete="RESTRICT"), nullable=False
    )
    tariff_id: Mapped[int] = mapped_column(
        ForeignKey("tariffs.id", ondelete="RESTRICT"), nullable=False
    )
    planned_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="bookingstatus"), nullable=False, default=BookingStatus.created
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="bookings", foreign_keys=[user_id])
    vehicle = relationship("Vehicle", back_populates="bookings")
    parking = relationship("Parking", back_populates="bookings")
    spot = relationship("ParkingSpot", back_populates="bookings")
    tariff = relationship("Tariff", back_populates="bookings")
    session = relationship(
        "ParkingSession", back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )
    payments = relationship("Payment", back_populates="booking")
