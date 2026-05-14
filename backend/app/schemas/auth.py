from pydantic import BaseModel, Field

from app.schemas.email_field import DemoEmail
from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: DemoEmail
    phone: str | None = None
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: DemoEmail
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# GET /auth/me returns UserRead (includes role)
AuthMeResponse = UserRead
