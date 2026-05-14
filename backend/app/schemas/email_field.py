"""Email for API payloads: allows demo domains like @parking.local (rejected by EmailStr)."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BeforeValidator


def _normalize_demo_email(v: Any) -> str:
    if not isinstance(v, str):
        raise TypeError("email must be a string")
    s = v.strip().lower()
    if "@" not in s or s.count("@") != 1:
        raise ValueError("Invalid email format")
    local, _, domain = s.partition("@")
    if not local or len(local) > 64:
        raise ValueError("Invalid email local part")
    if not domain or len(domain) > 253 or ".." in domain:
        raise ValueError("Invalid email domain")
    return s


DemoEmail = Annotated[str, BeforeValidator(_normalize_demo_email)]
