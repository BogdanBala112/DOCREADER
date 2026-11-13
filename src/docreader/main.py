"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from docreader.api.health import router as health_router
from docreader.core.config import Settings, get_settings
from docreader.infrastructure.database import create_database_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an independently configurable application instance."""
    runtime_settings = settings or get_settings()
    database_engine = create_database_engine(runtime_settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await database_engine.dispose()

    app = FastAPI(
        title=runtime_settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.database_engine = database_engine
    app.include_router(health_router)
    return app


app = create_app()
