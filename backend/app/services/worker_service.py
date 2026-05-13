from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.worker_assignment_repository import WorkerAssignmentRepository


def worker_parking_ids(db: Session, worker_id: int) -> list[int]:
    repo = WorkerAssignmentRepository(db)
    return repo.list_parking_ids_for_worker(worker_id)


def ensure_worker_parking(db: Session, worker_id: int, parking_id: int) -> None:
    """403 if worker is not assigned to the given parking."""
    repo = WorkerAssignmentRepository(db)
    ok = repo.is_assigned(worker_id, parking_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Worker is not assigned to this parking",
        )
