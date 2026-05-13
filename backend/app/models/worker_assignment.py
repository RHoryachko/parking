from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkerAssignment(Base):
    __tablename__ = "worker_assignments"
    __table_args__ = (
        UniqueConstraint("worker_id", "parking_id", name="uq_worker_parking_assignment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parking_id: Mapped[int] = mapped_column(
        ForeignKey("parkings.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    worker = relationship("User", back_populates="worker_assignments")
    parking = relationship("Parking", back_populates="worker_assignments")
