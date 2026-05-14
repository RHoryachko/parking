"""Simulated AI gate: vision (kie.ai Gemini) + parking session rules."""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.schemas.ai import AiGateSimulationResponse
from app.services.kie_vision_plate import recognize_plate_kie
from app.services.session_service import (
    find_active_session_by_parking_plate,
    find_paid_booking_for_entry,
    register_entry,
    register_exit,
)
from app.services.util import normalize_plate

MAX_IMAGE_BYTES = 12 * 1024 * 1024


def _vision_plate(cfg: Settings, image_bytes: bytes, mime: str) -> str:
    key = (cfg.KIE_AI_API_KEY or "").strip()
    if not key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "KIE_AI_API_KEY is not configured (kie.ai bearer token for Gemini vision)",
        )
    if not image_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty image file")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image too large (max 12MB)")
    try:
        raw = recognize_plate_kie(
            api_key=key,
            chat_url=(cfg.KIE_AI_CHAT_URL or "").strip(),
            model=(cfg.KIE_AI_MODEL or "gemini-2.5-flash").strip(),
            image_bytes=image_bytes,
            mime_type=mime or "image/jpeg",
        )
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    plate = normalize_plate(raw)
    if not plate:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Plate could not be read from the image (empty after normalization)",
        )
    return plate


def simulate_ai_gate_entry(
    db: Session, *, parking_id: int, image_bytes: bytes, mime: str, cfg: Settings | None = None
) -> AiGateSimulationResponse:
    """
    Recognize plate from image; if a matching paid booking exists on this parking, start session.
    """
    cfg = cfg or Settings()
    plate = _vision_plate(cfg, image_bytes, mime)
    booking = find_paid_booking_for_entry(
        db,
        parking_id=parking_id,
        plate=plate,
        require_inside_planned_window=False,
    )
    if not booking:
        return AiGateSimulationResponse(
            recognized_plate=plate,
            barrier_open=False,
            reason="no_paid_booking_or_spot_not_reserved",
        )
    try:
        sess = register_entry(
            db,
            parking_id=parking_id,
            plate_number=plate,
            require_inside_planned_window=False,
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_409_CONFLICT:
            return AiGateSimulationResponse(
                recognized_plate=plate,
                barrier_open=False,
                reason=str(exc.detail),
                booking_id=booking.id,
            )
        raise
    return AiGateSimulationResponse(
        recognized_plate=plate,
        barrier_open=True,
        reason="ok",
        booking_id=booking.id,
        session_id=sess.id,
    )


def simulate_ai_gate_exit(
    db: Session, *, parking_id: int, image_bytes: bytes, mime: str, cfg: Settings | None = None
) -> AiGateSimulationResponse:
    """Recognize plate; if an active session exists for this parking + plate, complete exit."""
    cfg = cfg or Settings()
    plate = _vision_plate(cfg, image_bytes, mime)
    sess = find_active_session_by_parking_plate(db, parking_id=parking_id, plate=plate)
    if not sess:
        return AiGateSimulationResponse(
            recognized_plate=plate,
            barrier_open=False,
            reason="no_active_session",
        )
    completed = register_exit(db, session_id=sess.id)
    tp: Decimal | None = completed.total_price
    price_str = str(tp) if tp is not None else None
    return AiGateSimulationResponse(
        recognized_plate=plate,
        barrier_open=True,
        reason="ok",
        booking_id=completed.booking_id,
        session_id=completed.id,
        total_price=price_str,
    )
