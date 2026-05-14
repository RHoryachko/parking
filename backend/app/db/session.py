from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base


def _is_sqlite(url: str) -> bool:
    return url.strip().lower().startswith("sqlite")


def _make_engine():
    url = settings.DATABASE_URL
    if _is_sqlite(url):
        # File DB + uvicorn reload: allow cross-thread connections
        connect_args: dict = {"check_same_thread": False}
        pool_kw: dict = {}
        if ":memory:" in url:
            pool_kw["poolclass"] = StaticPool
        return create_engine(url, connect_args=connect_args, **pool_kw)
    return create_engine(url, pool_pre_ping=True)


engine = _make_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Dev helper — production PostgreSQL uses Alembic."""
    Base.metadata.create_all(bind=engine)


def bootstrap_sqlite_schema() -> None:
    """Create tables from models (SQLite). PostgreSQL uses Alembic instead."""
    if not _is_sqlite(settings.DATABASE_URL):
        return
    Base.metadata.create_all(bind=engine)


def maybe_seed_empty_db() -> None:
    """If SQLite DB has no users, run idempotent seed (local dev)."""
    if not _is_sqlite(settings.DATABASE_URL):
        return
    from sqlalchemy import func, select

    from app.models.user import User

    db = SessionLocal()
    try:
        n = db.scalar(select(func.count()).select_from(User))
        if n == 0:
            from app.seeds.seed import run as seed_run

            seed_run()
    finally:
        db.close()
