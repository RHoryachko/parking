from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import SessionStatus


class ParkingSessionRead(BaseModel):
    id: int
    booking_id: int
    entry_time: datetime
    exit_time: datetime | None
    total_price: Decimal | None
    status: SessionStatus

    model_config = {"from_attributes": True}


class SessionEntryRequest(BaseModel):
    parking_id: int
    plate_number: str = Field(..., min_length=1, max_length=32)


class SessionExitRequest(BaseModel):
    session_id: int


class SessionCorrect(BaseModel):
    """Worker correction for mistakes (e.g. mark completed without payment capture here)."""

    status: SessionStatus | None = None
    exit_time: datetime | None = None
    total_price: Decimal | None = Field(None, ge=0)
