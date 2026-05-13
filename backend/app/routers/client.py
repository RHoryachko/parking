from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import distinct, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.models.booking import Booking
from app.models.enums import UserRole
from app.models.parking import Parking
from app.models.parking_spot import ParkingSpot
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.booking import BookingCreate, BookingRead
from app.schemas.payment import LiqPayCheckoutRead
from app.schemas.parking import ParkingDetailRead, ParkingRead
from app.schemas.spot import ParkingSpotRead
from app.schemas.user import UserRead, UserUpdate
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.services import booking_service
from app.services.util import normalize_plate

router = APIRouter(dependencies=[Depends(require_role(UserRole.client))])


@router.patch("/me", response_model=UserRead)
def patch_profile(
    payload: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    db.commit()
    db.refresh(user)
    return user


@router.get("/vehicles", response_model=list[VehicleRead])
def list_vehicles(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    rows = db.scalars(select(Vehicle).where(Vehicle.user_id == user.id)).all()
    return list(rows)


@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    v = Vehicle(
        user_id=user.id,
        plate_number=normalize_plate(payload.plate_number),
        brand=payload.brand,
        model=payload.model,
        color=payload.color,
    )
    db.add(v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Plate number already exists")
    db.refresh(v)
    return v


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    v = db.get(Vehicle, vehicle_id)
    if not v or v.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    if payload.plate_number is not None:
        v.plate_number = normalize_plate(payload.plate_number)
    if payload.brand is not None:
        v.brand = payload.brand
    if payload.model is not None:
        v.model = payload.model
    if payload.color is not None:
        v.color = payload.color
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Plate number already exists")
    db.refresh(v)
    return v


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    v = db.get(Vehicle, vehicle_id)
    if not v or v.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    db.delete(v)
    db.commit()
    return None


@router.get("/cities", response_model=list[str])
def list_cities(db: Annotated[Session, Depends(get_db)]):
    rows = db.scalars(select(distinct(Parking.city)).order_by(Parking.city)).all()
    return list(rows)


@router.get("/parkings", response_model=list[ParkingRead])
def list_parkings(
    db: Annotated[Session, Depends(get_db)],
    city: str | None = None,
):
    stmt = select(Parking).order_by(Parking.name)
    if city:
        stmt = stmt.where(Parking.city == city)
    rows = db.scalars(stmt).all()
    return list(rows)


@router.get("/parkings/{parking_id}", response_model=ParkingDetailRead)
def get_parking(parking_id: int, db: Annotated[Session, Depends(get_db)]):
    p = db.get(Parking, parking_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    return p


@router.get("/parkings/{parking_id}/spots", response_model=list[ParkingSpotRead])
def list_spots(parking_id: int, db: Annotated[Session, Depends(get_db)]):
    rows = db.scalars(
        select(ParkingSpot)
        .where(ParkingSpot.parking_id == parking_id)
        .order_by(ParkingSpot.code)
    ).all()
    return list(rows)


@router.post("/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking_route(
    payload: BookingCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    b = booking_service.create_booking(
        db,
        user=user,
        vehicle_id=payload.vehicle_id,
        parking_id=payload.parking_id,
        spot_id=payload.spot_id,
        tariff_id=payload.tariff_id,
        planned_start_time=payload.planned_start_time,
        planned_end_time=payload.planned_end_time,
    )
    db.commit()
    db.refresh(b)
    return b


@router.post("/bookings/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking_route(
    booking_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    b = booking_service.cancel_booking(db, user=user, booking_id=booking_id, is_admin=False)
    db.commit()
    db.refresh(b)
    return b


@router.post("/bookings/{booking_id}/liqpay-checkout", response_model=LiqPayCheckoutRead)
def liqpay_checkout_route(
    booking_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    url, payment_id = booking_service.start_liqpay_checkout(db, user=user, booking_id=booking_id)
    db.commit()
    return LiqPayCheckoutRead(checkout_url=url, payment_id=payment_id)


@router.post("/bookings/{booking_id}/pay", response_model=BookingRead)
def pay_booking_route(
    booking_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    b = booking_service.pay_booking_mock(db, user=user, booking_id=booking_id)
    db.commit()
    db.refresh(b)
    return b


@router.get("/bookings", response_model=list[BookingRead])
def booking_history(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.client))],
):
    rows = db.scalars(
        select(Booking)
        .where(Booking.user_id == user.id)
        .order_by(Booking.created_at.desc())
    ).all()
    return list(rows)
