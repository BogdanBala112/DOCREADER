"""PostgreSQL integration tests for embedding similarity search."""

import os

import pytest

from docreader.application.ingest import persist_text_document
from docreader.application.search import search_segments
from docreader.core.config import get_settings
from docreader.core.embeddings import EMBEDDING_DIMENSIONS
from docreader.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from docreader.infrastructure.models import Document
from docreader.ingestion.text import prepare_text_upload
from tests.hash_embedder import HashEmbeddingClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use the local PostgreSQL database",
    ),
]


async def test_search_returns_the_closest_segment_first() -> None:
    engine = create_database_engine(get_settings().database_url)
    session_factory = create_session_factory(engine)
    embedder = HashEmbeddingClient(EMBEDDING_DIMENSIONS)
    uploads = [
        prepare_text_upload(
            "interest.txt",
            b"Compound interest grows over time\n",
            max_bytes=1000,
        ),
        prepare_text_upload(
            "glossary.txt",
            b"The glossary defines unrelated words\n",
            max_bytes=1000,
        ),
    ]
    document_ids = []

    async with session_factory() as session:
        for upload in uploads:
            stored = await persist_text_document(session, upload, embedder)
            document_ids.append(stored.document_id)

    async with session_factory() as session:
        matches = await search_segments(
            session,
            embedder,
            "compound interest",
            limit=2,
            max_distance=0.5,
        )
        assert len(matches) == 1
        assert matches[0].title == "interest"
        assert "Compound interest" in matches[0].content
        assert matches[0].distance <= 0.5
        for document_id in document_ids:
            document = await session.get(Document, document_id)
            await session.delete(document)
        await session.commit()

    await engine.dispose()
