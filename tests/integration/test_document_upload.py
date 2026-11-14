"""PostgreSQL integration tests for document upload persistence."""

import os

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from docreader.application.ingest import persist_text_document
from docreader.core.config import get_settings
from docreader.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from docreader.infrastructure.models import Asset, Document
from docreader.ingestion.text import prepare_text_upload

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use the local PostgreSQL database",
    ),
]


async def test_text_upload_is_stored_and_can_be_removed() -> None:
    engine = create_database_engine(get_settings().database_url)
    session_factory = create_session_factory(engine)
    upload = prepare_text_upload(
        "notes.txt",
        b"Hello retrieval\n",
        max_bytes=1000,
    )

    async with session_factory() as session:
        stored = await persist_text_document(session, upload)

    async with session_factory() as session:
        query = (
            select(Document)
            .options(selectinload(Document.assets).selectinload(Asset.segments))
            .where(Document.id == stored.document_id)
        )
        document = (await session.execute(query)).scalar_one()

        assert document.title == "notes"
        assert document.assets[0].file_content == b"Hello retrieval\n"
        assert document.assets[0].segments[0].locator == {
            "line_end": 1,
            "line_start": 1,
        }
        await session.delete(document)
        await session.commit()

    await engine.dispose()
