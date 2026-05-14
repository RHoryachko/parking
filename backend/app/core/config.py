import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always resolve backend/.env (works when cwd is backend/ or when running from Docker WORKDIR /app)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        # So LIQPAY_PUBLIC_KEY= in .env does not override sandbox defaults with ""
        env_ignore_empty=True,
    )

    # Local dev without Docker: SQLite file next to cwd when starting from backend/
    # PostgreSQL (Docker / local): postgresql://parking:parking@localhost:5432/parking
    DATABASE_URL: str = "sqlite:///./parking.db"
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60
    # Comma-separated origins for browser admin
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:8080,http://localhost:8080"
    # Public base URL of this API (no trailing slash). LiqPay server_url must reach this host.
    APP_PUBLIC_API_URL: str = "http://127.0.0.1:8010"
    # Flutter web origin (same host as `flutter run --web-port`, default 8080). LiqPay result_url → …/payment-success
    CLIENT_APP_WEB_URL: str = "http://127.0.0.1:8080"
    # Override LiqPay return URL (optional). Empty = CLIENT_APP_WEB_URL + /payment-success
    LIQPAY_RESULT_URL: str = ""
    # LiqPay: set in backend/.env (see .env.example).
    LIQPAY_PUBLIC_KEY: str = ""
    LIQPAY_PRIVATE_KEY: str = ""


settings = Settings()


def _liqpay_dotenv_candidate_paths() -> list[Path]:
    """Ordered unique paths that may contain LIQPAY_* (dev: cwd/repo layout differs from server)."""
    out: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        try:
            key = str(p.resolve())
        except OSError:
            key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)

    override = (os.getenv("LIQPAY_DOTENV_PATH") or "").strip()
    if override:
        add(Path(override))
    add(_ENV_FILE)
    add(Path.cwd() / ".env")
    add(Path.cwd() / "backend" / ".env")
    add(_BACKEND_ROOT.parent / ".env")
    return out


def liqpay_keys() -> tuple[str, str]:
    """Return (public, private). Prefer Settings; if missing, read from .env file(s) only.

    Empty `LIQPAY_*` in the process environment can override pydantic's dotenv layer; reading
    files with `dotenv_values` avoids that shadowing. Tries several paths (see
    `_liqpay_dotenv_candidate_paths`) and optional `LIQPAY_DOTENV_PATH`.
    """
    s = Settings()
    pub = (s.LIQPAY_PUBLIC_KEY or "").strip()
    priv = (s.LIQPAY_PRIVATE_KEY or "").strip()
    if pub and priv:
        return pub, priv
    for path in _liqpay_dotenv_candidate_paths():
        if not path.is_file():
            continue
        try:
            raw = dotenv_values(path, encoding="utf-8")
        except OSError:
            continue
        pub = str(raw.get("LIQPAY_PUBLIC_KEY") or "").strip()
        priv = str(raw.get("LIQPAY_PRIVATE_KEY") or "").strip()
        if pub and priv:
            return pub, priv
    return "", ""


def get_cors_origins() -> list[str]:
    return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
