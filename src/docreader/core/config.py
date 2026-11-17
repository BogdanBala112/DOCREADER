"""Typed application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

from docreader.core.embeddings import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL


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
    embedding_model: str = EMBEDDING_MODEL
    embedding_dimensions: int = EMBEDDING_DIMENSIONS
    embedding_cache_dir: Path = Path(".cache/fastembed")
    retrieval_limit: int = 5
    retrieval_max_distance: float = Field(default=0.45, gt=0, le=2)
    chat_base_url: str = "http://localhost:1234/v1"
    chat_api_key: str = "lm-studio"
    chat_model: str = ""
    chat_timeout_seconds: float = 60

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
