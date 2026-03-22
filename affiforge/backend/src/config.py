from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	app_name: str = "AffiForge API"
	app_version: str = "0.1.0"
	environment: str = "development"
	database_url: str = "sqlite:///./affiforge.db"
	redis_url: str = "redis://localhost:6379/0"
	openai_api_key: str = ""
	claude_api_key: str = ""
	max_cost_per_task: float = 0.12
	api_rate_limit_per_minute: int = 30
	api_usage_alert_ratio: float = 0.8
	enable_api_guardrails: bool = True
	jwt_secret_key: str = "dev-change-me"
	jwt_algorithm: str = "HS256"
	access_token_expire_minutes: int = 60
	stripe_secret_key: str = ""
	stripe_webhook_secret: str = ""
	reddit_client_id: str = ""
	reddit_client_secret: str = ""
	reddit_user_agent: str = "affiforge/0.1"

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
	return Settings()


settings = get_settings()
