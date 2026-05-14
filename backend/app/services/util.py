"""Shared helpers for domain logic."""

from datetime import datetime, timezone


def normalize_plate(plate: str) -> str:
    return plate.upper().replace(" ", "").replace("-", "")


def as_utc(dt: datetime) -> datetime:
    """DB/SQLite may return naive datetimes; treat naive as UTC for arithmetic and comparisons."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
