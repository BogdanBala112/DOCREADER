"""Fill embeddings for segments stored before vector search was enabled."""

import asyncio

from sqlalchemy import select

from docreader.core.config import get_settings
from docreader.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from docreader.infrastructure.embeddings import EmbeddingClient, create_embedder
from docreader.infrastructure.models import Segment


async def embed_missing_segments(
    session_factory,
    embedder: EmbeddingClient,
    batch_size: int = 32,
) -> int:
    """Embed segments that do not yet have a vector and return how many changed."""
    updated = 0
    while True:
        async with session_factory() as session:
            segments = (
                await session.scalars(
                    select(Segment)
                    .where(Segment.embedding.is_(None))
                    .order_by(Segment.created_at)
                    .limit(batch_size)
                )
            ).all()
            if not segments:
                return updated
            vectors = await embedder.embed([segment.content for segment in segments])
            for segment, vector in zip(segments, vectors, strict=True):
                segment.embedding = vector
            await session.commit()
            updated += len(segments)


async def main() -> None:
    """Embed every segment currently missing a vector."""
    settings = get_settings()
    engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    embedder = create_embedder(
        settings.embedding_model,
        settings.embedding_dimensions,
        settings.embedding_cache_dir,
    )
    updated = await embed_missing_segments(session_factory, embedder)
    await engine.dispose()
    print(f"Embedded {updated} segments")


if __name__ == "__main__":
    asyncio.run(main())
