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


class AiGateSimulationResponse(BaseModel):
    """AI gate simulation: vision (kie.ai Gemini) + barrier decision (no real hardware)."""

    recognized_plate: str
    barrier_open: bool
    reason: str
    booking_id: int | None = None
    session_id: int | None = None
    total_price: str | None = Field(None, description="On exit: billed amount for the completed session")
