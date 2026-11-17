"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from docreader.api.ask import router as ask_router
from docreader.api.documents import router as documents_router
from docreader.api.health import router as health_router
from docreader.core.config import Settings, get_settings
from docreader.infrastructure.chat import OpenAICompatibleChatClient
from docreader.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from docreader.infrastructure.embeddings import EmbeddingClient, create_embedder


def create_app(
    settings: Settings | None = None,
    embedder: EmbeddingClient | None = None,
    chat: OpenAICompatibleChatClient | None = None,
) -> FastAPI:
    """Create an independently configurable application instance."""
    runtime_settings = settings or get_settings()
    database_engine = create_database_engine(runtime_settings.database_url)
    runtime_embedder = embedder or create_embedder(
        runtime_settings.embedding_model,
        runtime_settings.embedding_dimensions,
        runtime_settings.embedding_cache_dir,
    )
    runtime_chat = chat or OpenAICompatibleChatClient(
        base_url=runtime_settings.chat_base_url,
        api_key=runtime_settings.chat_api_key,
        model=runtime_settings.chat_model,
        timeout_seconds=runtime_settings.chat_timeout_seconds,
    )

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
    app.state.session_factory = create_session_factory(database_engine)
    app.state.embedder = runtime_embedder
    app.state.chat = runtime_chat
    app.include_router(health_router)
    app.include_router(documents_router)
    app.include_router(ask_router)
    return app


app = create_app()
