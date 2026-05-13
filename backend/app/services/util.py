"""Shared helpers for domain logic."""


def normalize_plate(plate: str) -> str:
    return plate.upper().replace(" ", "").replace("-", "")
