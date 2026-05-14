from pydantic import BaseModel

from app.schemas.booking import BookingWithPaymentsRead
from app.schemas.session import ParkingSessionRead
from app.schemas.spot import ParkingSpotRead
from app.schemas.vehicle import VehicleRead


class WorkerSpotBoardItem(BaseModel):
    """One parking spot with optional live booking / session context for the worker UI."""

    spot: ParkingSpotRead
    vehicle: VehicleRead | None = None
    booking: BookingWithPaymentsRead | None = None
    session: ParkingSessionRead | None = None
    overstay_minutes: int | None = None
