from pydantic import BaseModel, Field

from app.models.enums import SpotStatus


class ParkingSpotCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=32)
    status: SpotStatus = SpotStatus.free


class ParkingSpotUpdate(BaseModel):
    code: str | None = Field(None, min_length=1, max_length=32)
    status: SpotStatus | None = None


class ParkingSpotRead(BaseModel):
    id: int
    parking_id: int
    code: str
    status: SpotStatus

    model_config = {"from_attributes": True}
