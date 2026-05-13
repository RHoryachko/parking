from decimal import Decimal

from pydantic import BaseModel, Field


class TariffCreate(BaseModel):
    price_per_hour: Decimal = Field(..., ge=0)


class TariffUpdate(BaseModel):
    price_per_hour: Decimal | None = Field(None, ge=0)


class TariffRead(BaseModel):
    id: int
    parking_id: int
    price_per_hour: Decimal

    model_config = {"from_attributes": True}
