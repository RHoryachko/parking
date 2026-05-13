from pydantic import BaseModel


class LiqPayCheckoutRead(BaseModel):
    checkout_url: str
    payment_id: int
