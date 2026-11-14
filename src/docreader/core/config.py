"""Typed application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Runtime settings shared by the API and background workers."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DOCREADER"
    environment: str = "development"
    postgres_db: str = "docreader"
    postgres_user: str = "docreader"
    postgres_password: str = Field(repr=False)
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    max_upload_bytes: int = 10 * 1024 * 1024

    @property
    def database_url(self) -> URL:
        """Build an escaped SQLAlchemy URL without exposing the password."""
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings instance per process."""
    return Settings()
