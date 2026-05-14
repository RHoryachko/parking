from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.deps import get_db
from app.schemas.ai import AiCheckEntryRequest, AiCheckEntryResponse, AiGateSimulationResponse
from app.services import ai_gate_sim_service, ai_service

router = APIRouter()


@router.post("/check-entry", response_model=AiCheckEntryResponse, status_code=status.HTTP_200_OK)
def check_entry(
    payload: AiCheckEntryRequest,
    db: Annotated[Session, Depends(get_db)],
):
    allow, reason, vid, bid = ai_service.check_entry(
        db,
        parking_id=payload.parking_id,
        recognized_plate=payload.recognized_plate,
        confidence=payload.confidence,
    )
    db.commit()
    return AiCheckEntryResponse(allow=allow, reason=reason, vehicle_id=vid, booking_id=bid)


@router.post("/gate/entry", response_model=AiGateSimulationResponse)
async def ai_gate_entry_multipart(
    parking_id: Annotated[int, Form(..., description="Parking lot id")],
    file: Annotated[UploadFile, File(..., description="Photo of the vehicle / plate")],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Simulated AI worker at entry: sends image to kie.ai Gemini, reads `plate_number` JSON,
    then if a paid booking exists for that plate on this parking — starts a session (same as worker entry).
    Response `barrier_open` means the gate may open (no real barrier integration here).
    """
    data = await file.read()
    mime = file.content_type or "application/octet-stream"
    out = ai_gate_sim_service.simulate_ai_gate_entry(
        db, parking_id=parking_id, image_bytes=data, mime=mime, cfg=Settings()
    )
    db.commit()
    return out


@router.post("/gate/exit", response_model=AiGateSimulationResponse)
async def ai_gate_exit_multipart(
    parking_id: Annotated[int, Form(..., description="Parking lot id")],
    file: Annotated[UploadFile, File(..., description="Photo of the vehicle / plate")],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Simulated AI worker at exit: vision plate → active session on this parking → register exit (same as worker exit-by-plate).
    """
    data = await file.read()
    mime = file.content_type or "application/octet-stream"
    out = ai_gate_sim_service.simulate_ai_gate_exit(
        db, parking_id=parking_id, image_bytes=data, mime=mime, cfg=Settings()
    )
    db.commit()
    return out
