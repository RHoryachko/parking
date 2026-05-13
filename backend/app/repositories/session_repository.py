from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import SessionStatus
from app.models.parking_session import ParkingSession


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, session_id: int) -> ParkingSession | None:
        return self.db.get(ParkingSession, session_id)

    def list_active(self) -> list[ParkingSession]:
        return list(
            self.db.scalars(
                select(ParkingSession).where(ParkingSession.status == SessionStatus.active)
            ).all()
        )

    def create(self, **kwargs) -> ParkingSession:
        session = ParkingSession(**kwargs)
        self.db.add(session)
        self.db.flush()
        return session
