from decimal import Decimal

from pydantic import BaseModel


class AdminStatsRead(BaseModel):
    parkings_count: int
    spots_total: int
    bookings_total: int
    active_sessions: int
    revenue_today: Decimal
