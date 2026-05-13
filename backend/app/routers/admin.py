from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, require_role
from app.models.ai_log import AiLog
from app.models.barrier_log import BarrierLog
from app.models.enums import UserRole
from app.models.parking import Parking
from app.models.parking_spot import ParkingSpot
from app.models.tariff import Tariff
from app.models.user import User
from app.models.worker_assignment import WorkerAssignment
from app.schemas.logs import AiLogRead, BarrierLogRead
from app.schemas.parking import (
    ParkingCreate,
    ParkingDetailRead,
    ParkingRead,
    ParkingUpdate,
    ParkingWorkModeUpdate,
)
from app.schemas.spot import ParkingSpotCreate, ParkingSpotRead, ParkingSpotUpdate
from app.schemas.stats import AdminStatsRead
from app.schemas.tariff import TariffCreate, TariffRead, TariffUpdate
from app.schemas.user import UserRead, WorkerBlockUpdate, WorkerCreate, WorkerUpdate
from app.schemas.worker import WorkerAssignRequest
from app.core.security import hash_password
from app.services import stats_service

router = APIRouter(dependencies=[Depends(require_role(UserRole.admin))])


# --- Parkings ---


@router.get("/parkings", response_model=list[ParkingRead])
def list_parkings(db: Annotated[Session, Depends(get_db)]):
    rows = db.scalars(select(Parking).order_by(Parking.name)).all()
    return list(rows)


@router.post("/parkings", response_model=ParkingRead, status_code=status.HTTP_201_CREATED)
def create_parking(payload: ParkingCreate, db: Annotated[Session, Depends(get_db)]):
    p = Parking(
        name=payload.name,
        city=payload.city,
        address=payload.address,
        capacity=payload.capacity,
        latitude=payload.latitude,
        longitude=payload.longitude,
        work_mode=payload.work_mode,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/parkings/{parking_id}", response_model=ParkingDetailRead)
def get_parking(parking_id: int, db: Annotated[Session, Depends(get_db)]):
    p = db.scalars(
        select(Parking)
        .where(Parking.id == parking_id)
        .options(selectinload(Parking.tariffs))
    ).first()
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    return p


@router.patch("/parkings/{parking_id}", response_model=ParkingRead)
def update_parking(
    parking_id: int,
    payload: ParkingUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    p = db.get(Parking, parking_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    if payload.name is not None:
        p.name = payload.name
    if payload.city is not None:
        p.city = payload.city
    if payload.address is not None:
        p.address = payload.address
    if payload.capacity is not None:
        p.capacity = payload.capacity
    if payload.work_mode is not None:
        p.work_mode = payload.work_mode
    if payload.latitude is not None:
        p.latitude = payload.latitude
    if payload.longitude is not None:
        p.longitude = payload.longitude
    db.commit()
    db.refresh(p)
    return p


@router.delete("/parkings/{parking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parking(parking_id: int, db: Annotated[Session, Depends(get_db)]):
    p = db.get(Parking, parking_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    db.delete(p)
    db.commit()
    return None


@router.patch("/parkings/{parking_id}/work-mode", response_model=ParkingRead)
def set_work_mode(
    parking_id: int,
    payload: ParkingWorkModeUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    p = db.get(Parking, parking_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    p.work_mode = payload.work_mode
    db.commit()
    db.refresh(p)
    return p


# --- Spots ---


@router.get("/parkings/{parking_id}/spots", response_model=list[ParkingSpotRead])
def list_spots(parking_id: int, db: Annotated[Session, Depends(get_db)]):
    if not db.get(Parking, parking_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    rows = db.scalars(
        select(ParkingSpot)
        .where(ParkingSpot.parking_id == parking_id)
        .order_by(ParkingSpot.code)
    ).all()
    return list(rows)


@router.post(
    "/parkings/{parking_id}/spots",
    response_model=ParkingSpotRead,
    status_code=status.HTTP_201_CREATED,
)
def create_spot(
    parking_id: int,
    payload: ParkingSpotCreate,
    db: Annotated[Session, Depends(get_db)],
):
    if not db.get(Parking, parking_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    s = ParkingSpot(parking_id=parking_id, code=payload.code, status=payload.status)
    db.add(s)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Spot code already exists for this parking")
    db.refresh(s)
    return s


@router.patch("/parkings/{parking_id}/spots/{spot_id}", response_model=ParkingSpotRead)
def update_spot(
    parking_id: int,
    spot_id: int,
    payload: ParkingSpotUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    s = db.get(ParkingSpot, spot_id)
    if not s or s.parking_id != parking_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spot not found")
    if payload.code is not None:
        s.code = payload.code
    if payload.status is not None:
        s.status = payload.status
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Spot code conflict")
    db.refresh(s)
    return s


@router.delete("/parkings/{parking_id}/spots/{spot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spot(parking_id: int, spot_id: int, db: Annotated[Session, Depends(get_db)]):
    s = db.get(ParkingSpot, spot_id)
    if not s or s.parking_id != parking_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spot not found")
    db.delete(s)
    db.commit()
    return None


# --- Tariffs ---


@router.get("/parkings/{parking_id}/tariffs", response_model=list[TariffRead])
def list_tariffs(parking_id: int, db: Annotated[Session, Depends(get_db)]):
    if not db.get(Parking, parking_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    rows = db.scalars(select(Tariff).where(Tariff.parking_id == parking_id)).all()
    return list(rows)


@router.post(
    "/parkings/{parking_id}/tariffs",
    response_model=TariffRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tariff(
    parking_id: int,
    payload: TariffCreate,
    db: Annotated[Session, Depends(get_db)],
):
    if not db.get(Parking, parking_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    t = Tariff(parking_id=parking_id, price_per_hour=payload.price_per_hour)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.patch("/parkings/{parking_id}/tariffs/{tariff_id}", response_model=TariffRead)
def update_tariff(
    parking_id: int,
    tariff_id: int,
    payload: TariffUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    t = db.get(Tariff, tariff_id)
    if not t or t.parking_id != parking_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tariff not found")
    if payload.price_per_hour is not None:
        t.price_per_hour = payload.price_per_hour
    db.commit()
    db.refresh(t)
    return t


@router.delete("/parkings/{parking_id}/tariffs/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tariff(parking_id: int, tariff_id: int, db: Annotated[Session, Depends(get_db)]):
    t = db.get(Tariff, tariff_id)
    if not t or t.parking_id != parking_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tariff not found")
    db.delete(t)
    db.commit()
    return None


# --- Workers ---


@router.get("/workers", response_model=list[UserRead])
def list_workers(db: Annotated[Session, Depends(get_db)]):
    rows = db.scalars(select(User).where(User.role == UserRole.worker).order_by(User.email)).all()
    return list(rows)


@router.post("/workers", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_worker(payload: WorkerCreate, db: Annotated[Session, Depends(get_db)]):
    exists = db.scalar(select(User.id).where(User.email == str(payload.email).lower()))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")
    u = User(
        full_name=payload.full_name,
        email=str(payload.email).lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=UserRole.worker,
        is_blocked=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.patch("/workers/{worker_id}", response_model=UserRead)
def update_worker(
    worker_id: int,
    payload: WorkerUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    u = db.get(User, worker_id)
    if not u or u.role != UserRole.worker:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Worker not found")
    if payload.full_name is not None:
        u.full_name = payload.full_name
    if payload.phone is not None:
        u.phone = payload.phone
    if payload.password is not None:
        u.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/workers/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(worker_id: int, db: Annotated[Session, Depends(get_db)]):
    u = db.get(User, worker_id)
    if not u or u.role != UserRole.worker:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Worker not found")
    db.delete(u)
    db.commit()
    return None


@router.post("/workers/{worker_id}/assign", status_code=status.HTTP_201_CREATED)
def assign_worker(
    worker_id: int,
    payload: WorkerAssignRequest,
    db: Annotated[Session, Depends(get_db)],
):
    u = db.get(User, worker_id)
    if not u or u.role != UserRole.worker:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Worker not found")
    if not db.get(Parking, payload.parking_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parking not found")
    wa = WorkerAssignment(worker_id=worker_id, parking_id=payload.parking_id)
    db.add(wa)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Assignment already exists")
    return {"ok": True}


@router.patch("/workers/{worker_id}/block", response_model=UserRead)
def block_worker(
    worker_id: int,
    payload: WorkerBlockUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    u = db.get(User, worker_id)
    if not u or u.role != UserRole.worker:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Worker not found")
    u.is_blocked = payload.is_blocked
    db.commit()
    db.refresh(u)
    return u


# --- Stats & logs ---


@router.get("/stats", response_model=AdminStatsRead)
def get_stats(db: Annotated[Session, Depends(get_db)]):
    return stats_service.admin_stats(db)


@router.get("/logs/barrier", response_model=list[BarrierLogRead])
def list_barrier_logs(
    db: Annotated[Session, Depends(get_db)],
    parking_id: int | None = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
):
    stmt = select(BarrierLog).order_by(BarrierLog.created_at.desc()).offset(skip).limit(limit)
    if parking_id is not None:
        stmt = stmt.where(BarrierLog.parking_id == parking_id)
    return list(db.scalars(stmt).all())


@router.get("/logs/ai", response_model=list[AiLogRead])
def list_ai_logs(
    db: Annotated[Session, Depends(get_db)],
    parking_id: int | None = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
):
    stmt = select(AiLog).order_by(AiLog.created_at.desc()).offset(skip).limit(limit)
    if parking_id is not None:
        stmt = stmt.where(AiLog.parking_id == parking_id)
    return list(db.scalars(stmt).all())
