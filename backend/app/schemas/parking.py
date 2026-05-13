from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import WorkMode


class ParkingCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=128)
    address: str = Field(..., min_length=1, max_length=512)
    capacity: int = Field(..., ge=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    work_mode: WorkMode = WorkMode.manual


class ParkingUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    capacity: int | None = Field(None, ge=1)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    work_mode: WorkMode | None = None


class ParkingRead(BaseModel):
    id: int
    name: str
    city: str
    address: str
    capacity: int
    latitude: float
    longitude: float
    work_mode: WorkMode
    created_at: datetime

    model_config = {"from_attributes": True}


class ParkingWorkModeUpdate(BaseModel):
    work_mode: WorkMode


class TariffNested(BaseModel):
    id: int
    price_per_hour: Decimal

    model_config = {"from_attributes": True}


class ParkingDetailRead(ParkingRead):
    tariffs: list[TariffNested] = Field(default_factory=list)
