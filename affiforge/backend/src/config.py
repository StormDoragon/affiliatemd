from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AffiForge API"
    app_version: str = "0.2.0"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./affiforge.db"
    redis_url: str = "redis://localhost:6379/0"
    app_origin: str = "http://localhost:3000"
    demo_mode: bool = False
    allow_registration: bool = False
    openai_api_key: str = ""
    claude_api_key: str = ""
    max_cost_per_task: float = Field(default=0.12, gt=0)
    api_rate_limit_per_minute: int = Field(default=30, ge=1)
    api_usage_alert_ratio: float = 0.8
    enable_api_guardrails: bool = True
    jwt_secret_key: str = "local-development-only-signing-key"
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    credential_encryption_key: str = ""
    stripe_secret_key: str = ""
    stripe_price_ids: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "AffiForge/0.2"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True
    )

    @property
    def production(self) -> bool:
        return self.environment == "production"

    @property
    def billing_prices(self) -> set[str]:
        return {item.strip() for item in self.stripe_price_ids.split(",") if item.strip()}

    @model_validator(mode="after")
    def validate_runtime(self):
        if self.credential_encryption_key:
            Fernet(self.credential_encryption_key.encode())
        if self.production:
            if self.demo_mode or not self.enable_api_guardrails:
                raise ValueError("Production requires live mode and API guardrails")
            if not self.database_url.startswith(
                ("postgresql://", "postgresql+psycopg://", "postgres://")
            ):
                raise ValueError("Production requires PostgreSQL")
            if (
                len(self.jwt_secret_key) < 32
                or self.jwt_secret_key.startswith("local-")
                or not self.credential_encryption_key
            ):
                raise ValueError("Set a strong JWT_SECRET_KEY and CREDENTIAL_ENCRYPTION_KEY")
            origin = urlsplit(self.app_origin)
            if (
                origin.scheme != "https"
                or not origin.hostname
                or origin.path
                or origin.query
                or origin.fragment
                or origin.username
            ):
                raise ValueError("APP_ORIGIN must be a bare HTTPS origin")
            if bool(self.stripe_secret_key) != bool(self.billing_prices):
                raise ValueError(
                    "Configure both STRIPE_SECRET_KEY and STRIPE_PRICE_IDS to enable billing"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
