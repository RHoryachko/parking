from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.parking import Parking
from app.models.parking_session import ParkingSession
from app.models.parking_spot import ParkingSpot
from app.models.enums import PaymentStatus, SessionStatus
from app.models.payment import Payment


def admin_stats(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    parkings_count = db.scalar(select(func.count()).select_from(Parking)) or 0
    spots_total = db.scalar(select(func.count()).select_from(ParkingSpot)) or 0
    bookings_total = db.scalar(select(func.count()).select_from(Booking)) or 0
    active_sessions = (
        db.scalar(
            select(func.count())
            .select_from(ParkingSession)
            .where(ParkingSession.status == SessionStatus.active)
        )
        or 0
    )
    revenue_today = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.paid,
            Payment.paid_at.isnot(None),
            Payment.paid_at >= today_start,
        )
    )
    if revenue_today is None:
        revenue_today = Decimal("0")

    return {
        "parkings_count": int(parkings_count),
        "spots_total": int(spots_total),
        "bookings_total": int(bookings_total),
        "active_sessions": int(active_sessions),
        "revenue_today": Decimal(revenue_today).quantize(Decimal("0.01")),
    }
