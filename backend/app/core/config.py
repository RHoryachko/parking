from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql://parking:parking@localhost:5432/parking"
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60
    # Comma-separated origins for browser admin
    CORS_ORIGINS: str = "http://localhost:5173"
    # Public base URL of this API (no trailing slash). LiqPay server_url must reach this host.
    APP_PUBLIC_API_URL: str = "http://127.0.0.1:8000"
    # Where LiqPay redirects the payer after checkout (admin or mobile deep link).
    LIQPAY_RESULT_URL: str = "http://localhost:5173/admin/parkings"
    LIQPAY_PUBLIC_KEY: str = ""
    LIQPAY_PRIVATE_KEY: str = ""


settings = Settings()


def get_cors_origins() -> list[str]:
    return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
