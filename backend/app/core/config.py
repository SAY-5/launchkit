from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://launchkit:launchkit@localhost:5432/launchkit"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = "price_test"

    # Provider seam: when set to "fake" the feature uses a deterministic local
    # provider and makes no network calls. Used in CI and local development.
    provider_mode: str = "fake"
    provider_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
