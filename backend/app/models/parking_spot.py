from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SpotStatus


class ParkingSpot(Base):
    __tablename__ = "parking_spots"
    __table_args__ = (UniqueConstraint("parking_id", "code", name="uq_spot_parking_code"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parking_id: Mapped[int] = mapped_column(
        ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[SpotStatus] = mapped_column(
        Enum(SpotStatus, name="spotstatus"), nullable=False, default=SpotStatus.free
    )

    parking = relationship("Parking", back_populates="spots")
    bookings = relationship("Booking", back_populates="spot")
