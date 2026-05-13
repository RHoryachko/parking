from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parking_id: Mapped[int] = mapped_column(
        ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    parking = relationship("Parking", back_populates="tariffs")
    bookings = relationship("Booking", back_populates="tariff")
