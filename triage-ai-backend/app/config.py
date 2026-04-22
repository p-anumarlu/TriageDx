from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "triage.ai"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./triage.db"

    # ── Auth ─────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # ── Google AI Studio ─────────────────────────────────────────────────────
    GOOGLE_AI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GOOGLE_MAPS_API_KEY: str = ""
    API_KEY: str = ""

    # ── HIPAA / Compliance ────────────────────────────────────────────────────
    HIPAA_AUDIT_LOG: bool = True

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
