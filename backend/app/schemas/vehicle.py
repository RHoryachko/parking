from pydantic import BaseModel, Field


class VehicleCreate(BaseModel):
    plate_number: str = Field(..., min_length=1, max_length=32)
    brand: str | None = None
    model: str | None = None
    color: str | None = None


class VehicleUpdate(BaseModel):
    plate_number: str | None = Field(None, min_length=1, max_length=32)
    brand: str | None = None
    model: str | None = None
    color: str | None = None


class VehicleRead(BaseModel):
    id: int
    user_id: int
    plate_number: str
    brand: str | None
    model: str | None
    color: str | None

    model_config = {"from_attributes": True}


class WorkerVehicleClientSummary(BaseModel):
    """Owner profile for worker plate search (no secrets)."""

    id: int
    full_name: str
    email: str
    phone: str | None

    model_config = {"from_attributes": True}


class VehicleWithClientRead(VehicleRead):
    client: WorkerVehicleClientSummary
