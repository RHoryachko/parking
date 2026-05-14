from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_log import AiLog
from app.models.vehicle import Vehicle
from app.services.session_service import find_paid_booking_for_entry, register_entry
from app.services.util import normalize_plate


def check_entry(
    db: Session,
    *,
    parking_id: int,
    recognized_plate: str,
    confidence: float | None = None,
) -> tuple[bool, str, int | None, int | None]:
    """
    AI gate decision + log.
    On allow, performs the same DB updates as worker entry (session, booking used, spot occupied).
    """
    _ = confidence  # reserved for future use (e.g. thresholding)

    norm = normalize_plate(recognized_plate)
    vehicle = db.scalar(select(Vehicle).where(Vehicle.plate_number == norm))
    booking = find_paid_booking_for_entry(
        db,
        parking_id=parking_id,
        plate=recognized_plate,
        require_inside_planned_window=True,
    )

    if vehicle is None:
        allowed, reason = False, "vehicle_not_found"
    elif booking is None:
        allowed, reason = False, "no_paid_booking_or_spot_not_reserved"
    else:
        allowed, reason = True, "ok"

    db.add(
        AiLog(
            parking_id=parking_id,
            vehicle_id=vehicle.id if vehicle else None,
            recognized_plate=norm,
            access_allowed=allowed,
        )
    )

    booking_id: int | None = None
    vid = vehicle.id if vehicle else None
    if allowed:
        register_entry(
            db,
            parking_id=parking_id,
            plate_number=recognized_plate,
            require_inside_planned_window=True,
        )
        booking_id = booking.id

    db.flush()
    return allowed, reason, vid, booking_id
