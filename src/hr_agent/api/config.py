from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # server
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_reload: bool = False

    # CORS — comma-separated list in env, e.g. "http://localhost:8501"
    cors_origins: str = "http://localhost:8501"

    # auth (stub for now; real JWT in a later step)
    jwt_secret: str = Field(default="dev-only-change-me", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    @property                                   # ← this is what was missing
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache()
def get_api_settings() -> APISettings:
    return APISettings()