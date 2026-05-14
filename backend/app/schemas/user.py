from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import UserRole
from app.schemas.email_field import DemoEmail


class UserRead(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None
    role: UserRole
    is_blocked: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkerRead(UserRead):
    """Worker row with parking assignments (admin list)."""

    assigned_parking_ids: list[int] = []


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = None


class WorkerCreate(BaseModel):
    full_name: str
    email: DemoEmail
    phone: str | None = None
    password: str = Field(..., min_length=6)


class WorkerUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    password: str | None = Field(None, min_length=6)


class WorkerBlockUpdate(BaseModel):
    is_blocked: bool
