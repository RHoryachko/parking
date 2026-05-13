from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import BarrierAction


class BarrierLog(Base):
    __tablename__ = "barrier_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parking_id: Mapped[int] = mapped_column(
        ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )
    worker_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[BarrierAction] = mapped_column(
        Enum(BarrierAction, name="barrieraction"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    parking = relationship("Parking", back_populates="barrier_logs")
    vehicle = relationship("Vehicle")
    worker = relationship("User")
