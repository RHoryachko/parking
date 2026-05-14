from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import BookingStatus, PaymentStatus


class BookingCreate(BaseModel):
    vehicle_id: int
    parking_id: int
    spot_id: int
    tariff_id: int
    planned_start_time: datetime
    planned_end_time: datetime

    @model_validator(mode="after")
    def check_times(self):
        if self.planned_end_time <= self.planned_start_time:
            raise ValueError("planned_end_time must be after planned_start_time")
        return self


class BookingRead(BaseModel):
    id: int
    user_id: int
    vehicle_id: int
    parking_id: int
    spot_id: int
    tariff_id: int
    planned_start_time: datetime
    planned_end_time: datetime
    status: BookingStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentInfoRead(BaseModel):
    id: int
    amount: Decimal
    status: PaymentStatus
    paid_at: datetime | None

    model_config = {"from_attributes": True}


class BookingWithPaymentsRead(BookingRead):
    payments: list[PaymentInfoRead] = Field(default_factory=list)


class WorkerBookingCreate(BaseModel):
    """Worker registers a client reservation (unpaid until POST /worker/bookings/{id}/pay)."""

    user_id: int = Field(..., description="Client (vehicle owner) user id")
    vehicle_id: int
    parking_id: int
    spot_id: int
    tariff_id: int
    planned_start_time: datetime
    planned_end_time: datetime

    @model_validator(mode="after")
    def check_times(self):
        if self.planned_end_time <= self.planned_start_time:
            raise ValueError("planned_end_time must be after planned_start_time")
        return self


class ManualBookingCreate(BaseModel):
    """Worker creates an already-paid reservation (walk-in)."""

    user_id: int = Field(..., description="Client (vehicle owner) user id")
    vehicle_id: int
    parking_id: int
    spot_id: int
    tariff_id: int
    planned_start_time: datetime
    planned_end_time: datetime

    @model_validator(mode="after")
    def check_times(self):
        if self.planned_end_time <= self.planned_start_time:
            raise ValueError("planned_end_time must be after planned_start_time")
        return self
