from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.worker_assignment import WorkerAssignment


class WorkerAssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_parking_ids_for_worker(self, worker_id: int) -> list[int]:
        return list(
            self.db.scalars(
                select(WorkerAssignment.parking_id).where(
                    WorkerAssignment.worker_id == worker_id
                )
            ).all()
        )

    def is_assigned(self, worker_id: int, parking_id: int) -> bool:
        return bool(
            self.db.scalar(
                select(WorkerAssignment.id).where(
                    WorkerAssignment.worker_id == worker_id,
                    WorkerAssignment.parking_id == parking_id,
                )
            )
        )

    def create(self, **kwargs) -> WorkerAssignment:
        assignment = WorkerAssignment(**kwargs)
        self.db.add(assignment)
        self.db.flush()
        return assignment
