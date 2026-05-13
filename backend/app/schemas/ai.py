from pydantic import BaseModel, Field


class AiCheckEntryRequest(BaseModel):
    parking_id: int
    recognized_plate: str = Field(..., min_length=1, max_length=64)
    confidence: float | None = Field(None, ge=0, le=1)


class AiCheckEntryResponse(BaseModel):
    allow: bool
    reason: str
    vehicle_id: int | None = None
    booking_id: int | None = None
