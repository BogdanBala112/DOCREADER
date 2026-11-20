"""Search stored segments by embedding similarity."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docreader.infrastructure.embeddings import EmbeddingClient, EmbeddingError
from docreader.infrastructure.models import Asset, Document, Segment


@dataclass(frozen=True)
class RetrievedSegment:
    """A matching passage and the document it came from."""

    document_id: UUID
    title: str
    filename: str
    position: int
    content: str
    line_start: int
    line_end: int
    distance: float


async def search_segments(
    session: AsyncSession,
    embedder: EmbeddingClient,
    question: str,
    limit: int,
    max_distance: float,
    document_ids: list[UUID] | None = None,
) -> list[RetrievedSegment]:
    """Return embedded segments within the maximum cosine distance.

    Pass document_ids to restrict results to those documents only.
    """
    vector = (await embedder.embed([question]))[0]
    if len(vector) != embedder.dimensions:
        raise EmbeddingError(
            "Embedding provider returned a vector with the wrong dimensions"
        )

    distance = Segment.embedding.cosine_distance(vector)
    statement = (
        select(
            Segment,
            Document.id,
            Document.title,
            Asset.original_filename,
            distance.label("distance"),
        )
        .join(Asset, Segment.asset_id == Asset.id)
        .join(Document, Asset.document_id == Document.id)
        .where(Segment.embedding.is_not(None))
        .where(distance <= max_distance)
        .order_by(distance)
        .limit(limit)
    )
    if document_ids:
        statement = statement.where(Document.id.in_(document_ids))
    rows = (await session.execute(statement)).all()
    return [
        RetrievedSegment(
            document_id=document_id,
            title=title,
            filename=filename,
            position=segment.position,
            content=segment.content,
            line_start=int(segment.locator["line_start"]),
            line_end=int(segment.locator["line_end"]),
            distance=float(row_distance),
        )
        for segment, document_id, title, filename, row_distance in rows
    ]
