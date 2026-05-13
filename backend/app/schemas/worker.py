from pydantic import BaseModel, Field

from app.models.enums import BarrierAction


class BarrierRequest(BaseModel):
    parking_id: int
    action: BarrierAction
    vehicle_id: int | None = None


class WorkerAssignRequest(BaseModel):
    parking_id: int
