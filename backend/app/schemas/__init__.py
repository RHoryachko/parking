from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.booking import BookingCreate, BookingRead
from app.schemas.parking import ParkingCreate, ParkingRead, ParkingUpdate
from app.schemas.session import ParkingSessionRead, SessionCorrect
from app.schemas.spot import ParkingSpotCreate, ParkingSpotRead, ParkingSpotUpdate
from app.schemas.tariff import TariffCreate, TariffRead, TariffUpdate
from app.schemas.user import UserRead, UserUpdate
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate

__all__ = [
    "BookingCreate",
    "BookingRead",
    "LoginRequest",
    "ParkingCreate",
    "ParkingRead",
    "ParkingSessionRead",
    "ParkingSpotCreate",
    "ParkingSpotRead",
    "ParkingSpotUpdate",
    "ParkingUpdate",
    "RegisterRequest",
    "SessionCorrect",
    "TariffCreate",
    "TariffRead",
    "TariffUpdate",
    "TokenResponse",
    "UserRead",
    "UserUpdate",
    "VehicleCreate",
    "VehicleRead",
    "VehicleUpdate",
]
