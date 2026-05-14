from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.deps import get_db, require_role
from app.models.barrier_log import BarrierLog
from app.models.booking import Booking
from app.models.enums import SessionStatus, UserRole
from app.models.parking import Parking
from app.models.parking_session import ParkingSession
from app.models.parking_spot import ParkingSpot
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.booking import (
    BookingRead,
    BookingWithPaymentsRead,
    ManualBookingCreate,
    WorkerBookingCreate,
)
from app.schemas.parking import ParkingDetailRead, ParkingRead
from app.schemas.session import (
    ParkingSessionRead,
    SessionCorrect,
    SessionEntryRequest,
    SessionExitRequest,
)
from app.schemas.spot import ParkingSpotRead
from app.schemas.vehicle import VehicleRead
from app.schemas.worker import BarrierRequest
from app.schemas.worker_board import WorkerSpotBoardItem
from app.services import booking_service, session_service, worker_board_service, worker_service
from app.services.util import normalize_plate

router = APIRouter(dependencies=[Depends(require_role(UserRole.worker))])


@router.get("/parkings", response_model=list[ParkingRead])
def list_worker_parkings(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    assigned = worker_service.worker_parking_ids(db, user.id)
    if not assigned:
        return []
    rows = db.scalars(select(Parking).where(Parking.id.in_(assigned)).order_by(Parking.name)).all()
    return list(rows)


@router.get("/parkings/{parking_id}/spot-board", response_model=list[WorkerSpotBoardItem])
def worker_spot_board(
    parking_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    worker_service.ensure_worker_parking(db, user.id, parking_id)
    if not db.get(Parking, parking_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    return worker_board_service.list_parking_spot_board(db, parking_id=parking_id)


@router.get("/parkings/{parking_id}", response_model=ParkingDetailRead)
def worker_parking_detail(
    parking_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    worker_service.ensure_worker_parking(db, user.id, parking_id)
    p = db.scalars(
        select(Parking).where(Parking.id == parking_id).options(selectinload(Parking.tariffs))
    ).first()
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    return p


@router.post("/bookings", response_model=BookingWithPaymentsRead, status_code=status.HTTP_201_CREATED)
def worker_create_unpaid_booking(
    payload: WorkerBookingCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    worker_service.ensure_worker_parking(db, user.id, payload.parking_id)
    b = booking_service.create_booking_for_client(
        db,
        client_user_id=payload.user_id,
        vehicle_id=payload.vehicle_id,
        parking_id=payload.parking_id,
        spot_id=payload.spot_id,
        tariff_id=payload.tariff_id,
        planned_start_time=payload.planned_start_time,
        planned_end_time=payload.planned_end_time,
    )
    db.commit()
    stmt = select(Booking).where(Booking.id == b.id).options(joinedload(Booking.payments))
    out = db.scalars(stmt).first()
    return out


@router.post("/bookings/{booking_id}/pay", response_model=BookingRead)
def worker_pay_booking(
    booking_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    b = booking_service.pay_booking_worker_mock(db, worker_id=user.id, booking_id=booking_id)
    db.commit()
    db.refresh(b)
    return b


@router.get("/spots", response_model=list[ParkingSpotRead])
def list_assigned_spots(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
    parking_id: int | None = None,
):
    assigned = worker_service.worker_parking_ids(db, user.id)
    if parking_id is not None:
        worker_service.ensure_worker_parking(db, user.id, parking_id)
        stmt = (
            select(ParkingSpot)
            .where(ParkingSpot.parking_id == parking_id)
            .order_by(ParkingSpot.code)
        )
    else:
        if not assigned:
            return []
        stmt = (
            select(ParkingSpot)
            .where(ParkingSpot.parking_id.in_(assigned))
            .order_by(ParkingSpot.parking_id, ParkingSpot.code)
        )
    return list(db.scalars(stmt).all())


@router.get("/sessions/active", response_model=list[ParkingSessionRead])
def list_active_sessions(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
    parking_id: int | None = None,
):
    assigned = worker_service.worker_parking_ids(db, user.id)
    stmt = (
        select(ParkingSession)
        .join(Booking, Booking.id == ParkingSession.booking_id)
        .where(ParkingSession.status == SessionStatus.active)
    )
    if parking_id is not None:
        worker_service.ensure_worker_parking(db, user.id, parking_id)
        stmt = stmt.where(Booking.parking_id == parking_id)
    elif assigned:
        stmt = stmt.where(Booking.parking_id.in_(assigned))
    else:
        return []
    rows = db.scalars(stmt.order_by(ParkingSession.entry_time.desc())).all()
    return list(rows)


@router.get("/vehicles/search", response_model=list[VehicleRead])
def search_vehicle_by_plate(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
    plate: str = Query(..., min_length=1),
):
    _ = user
    norm = normalize_plate(plate)
    rows = db.scalars(select(Vehicle).where(Vehicle.plate_number == norm)).all()
    return list(rows)


@router.get("/bookings/by-plate", response_model=BookingWithPaymentsRead | None)
def check_booking_payment_by_plate(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
    plate: str = Query(..., min_length=1),
    parking_id: int = Query(...),
):
    worker_service.ensure_worker_parking(db, user.id, parking_id)
    norm = normalize_plate(plate)
    vehicle = db.scalar(select(Vehicle).where(Vehicle.plate_number == norm))
    if not vehicle:
        return None
    stmt = (
        select(Booking)
        .where(Booking.vehicle_id == vehicle.id, Booking.parking_id == parking_id)
        .options(joinedload(Booking.payments))
        .order_by(Booking.created_at.desc())
        .limit(1)
    )
    booking = db.scalars(stmt).first()
    return booking


@router.post("/bookings/manual", response_model=BookingWithPaymentsRead, status_code=status.HTTP_201_CREATED)
def create_manual_booking(
    payload: ManualBookingCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    worker_service.ensure_worker_parking(db, user.id, payload.parking_id)
    b = booking_service.create_manual_paid_booking(
        db,
        vehicle_id=payload.vehicle_id,
        parking_id=payload.parking_id,
        spot_id=payload.spot_id,
        tariff_id=payload.tariff_id,
        planned_start_time=payload.planned_start_time,
        planned_end_time=payload.planned_end_time,
        client_user_id=payload.user_id,
    )
    db.commit()
    stmt = (
        select(Booking)
        .where(Booking.id == b.id)
        .options(joinedload(Booking.payments))
    )
    out = db.scalars(stmt).first()
    return out


@router.post("/entry", response_model=ParkingSessionRead, status_code=status.HTTP_201_CREATED)
def register_entry_route(
    payload: SessionEntryRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    worker_service.ensure_worker_parking(db, user.id, payload.parking_id)
    s = session_service.register_entry(
        db, parking_id=payload.parking_id, plate_number=payload.plate_number
    )
    db.commit()
    db.refresh(s)
    return s


@router.post("/exit", response_model=ParkingSessionRead)
def register_exit_route(
    payload: SessionExitRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    s = db.get(ParkingSession, payload.session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    worker_service.ensure_worker_parking(db, user.id, s.booking.parking_id)
    s = session_service.register_exit(db, session_id=payload.session_id)
    db.commit()
    db.refresh(s)
    return s


@router.post("/exit-by-plate", response_model=ParkingSessionRead)
def register_exit_by_plate_route(
    payload: SessionEntryRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    """Complete the active session for this parking + plate (worker registers exit at barrier)."""
    worker_service.ensure_worker_parking(db, user.id, payload.parking_id)
    s = session_service.find_active_session_by_parking_plate(
        db, parking_id=payload.parking_id, plate=payload.plate_number
    )
    if not s:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No active parking session for this plate at this parking",
        )
    out = session_service.register_exit(db, session_id=s.id)
    db.commit()
    db.refresh(out)
    return out


@router.post("/barrier", status_code=status.HTTP_201_CREATED)
def barrier_action(
    payload: BarrierRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    worker_service.ensure_worker_parking(db, user.id, payload.parking_id)
    log = BarrierLog(
        parking_id=payload.parking_id,
        vehicle_id=payload.vehicle_id,
        worker_id=user.id,
        action=payload.action,
    )
    db.add(log)
    db.commit()
    return {"ok": True}


@router.patch("/sessions/{session_id}", response_model=ParkingSessionRead)
def correct_session_route(
    session_id: int,
    payload: SessionCorrect,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_role(UserRole.worker))],
):
    s = db.get(ParkingSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    worker_service.ensure_worker_parking(db, user.id, s.booking.parking_id)
    s = session_service.correct_session(
        db,
        session_id=session_id,
        new_status=payload.status,
        exit_time=payload.exit_time,
        total_price=payload.total_price,
    )
    db.commit()
    db.refresh(s)
    return s
