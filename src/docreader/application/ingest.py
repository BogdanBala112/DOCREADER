"""Persist a validated text upload and its extracted segments."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from docreader.infrastructure.embeddings import EmbeddingClient
from docreader.infrastructure.models import Asset, Document, Segment
from docreader.ingestion.text import PreparedTextUpload


@dataclass(frozen=True)
class StoredDocument:
    """Identifiers and counts returned after a successful upload."""

    document_id: UUID
    title: str
    filename: str
    media_type: str
    version_number: int
    segment_count: int


async def persist_text_document(
    session: AsyncSession,
    upload: PreparedTextUpload,
    embedder: EmbeddingClient,
) -> StoredDocument:
    """Store the original file, document, asset, and segments atomically."""
    vectors = await embedder.embed([segment.content for segment in upload.segments])
    document = Document(title=upload.title)
    asset = Asset(
        document=document,
        version_number=1,
        original_filename=upload.filename,
        media_type=upload.media_type,
        file_content=upload.data,
        sha256=upload.content_hash,
        byte_size=len(upload.data),
    )
    asset.segments.extend(
        Segment(
            position=segment.position,
            content=segment.content,
            embedding=vector,
            token_count=segment.token_count,
            locator={
                "line_start": segment.line_start,
                "line_end": segment.line_end,
            },
        )
        for segment, vector in zip(upload.segments, vectors, strict=True)
    )
    session.add(document)
    await session.commit()

    return StoredDocument(
        document_id=document.id,
        title=document.title,
        filename=asset.original_filename,
        media_type=asset.media_type,
        version_number=asset.version_number,
        segment_count=len(asset.segments),
    )
