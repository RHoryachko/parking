from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.ai import AiCheckEntryRequest, AiCheckEntryResponse
from app.services import ai_service

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
