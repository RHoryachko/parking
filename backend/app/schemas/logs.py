from datetime import datetime

from pydantic import BaseModel

from app.models.enums import BarrierAction


class BarrierLogRead(BaseModel):
    id: int
    parking_id: int
    vehicle_id: int | None
    worker_id: int | None
    action: BarrierAction
    created_at: datetime

    model_config = {"from_attributes": True}


class AiLogRead(BaseModel):
    id: int
    parking_id: int
    vehicle_id: int | None
    recognized_plate: str
    access_allowed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
