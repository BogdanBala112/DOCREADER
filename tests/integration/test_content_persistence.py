"""PostgreSQL integration tests for normalized content persistence."""

import os

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from docreader.core.config import get_settings
from docreader.infrastructure.database import create_database_engine
from docreader.infrastructure.models import Asset, Document, Segment

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 to use the local PostgreSQL database",
    ),
]


async def test_document_asset_and_segments_round_trip() -> None:
    engine = create_database_engine(get_settings().database_url)

    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        try:
            document = Document(title="RAG fundamentals")
            asset = Asset(
                document=document,
                version_number=1,
                original_filename="rag-fundamentals.txt",
                media_type="text/plain",
                file_content=b"x" * 42,
                sha256="a" * 64,
                byte_size=42,
            )
            asset.segments.extend(
                [
                    Segment(
                        position=0,
                        content="Retrieval finds relevant source material.",
                        token_count=6,
                        locator={"line_start": 1, "line_end": 1},
                    ),
                    Segment(
                        position=1,
                        content="Generation answers from the retrieved context.",
                        token_count=7,
                        locator={"line_start": 2, "line_end": 2},
                    ),
                ]
            )
            session.add(document)
            await session.flush()

            query = (
                select(Document)
                .options(selectinload(Document.assets).selectinload(Asset.segments))
                .where(Document.id == document.id)
            )
            stored_document = (await session.execute(query)).scalar_one()

            assert stored_document.title == "RAG fundamentals"
            assert len(stored_document.assets) == 1
            assert [
                segment.position for segment in stored_document.assets[0].segments
            ] == [0, 1]
            assert stored_document.assets[0].segments[0].locator == {
                "line_end": 1,
                "line_start": 1,
            }
        finally:
            await session.close()
            await transaction.rollback()

    await engine.dispose()
