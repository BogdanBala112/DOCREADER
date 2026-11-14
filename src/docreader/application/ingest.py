"""Persist a validated text upload and its extracted segments."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from docreader.infrastructure.models import Asset, Document, Segment
from docreader.ingestion.text import PreparedTextUpload


class StoredDocument:
    """Identifiers and counts returned after a successful upload."""

    def __init__(
        self,
        document_id: UUID,
        title: str,
        filename: str,
        media_type: str,
        version_number: int,
        segment_count: int,
    ) -> None:
        self.document_id = document_id
        self.title = title
        self.filename = filename
        self.media_type = media_type
        self.version_number = version_number
        self.segment_count = segment_count


async def persist_text_document(
    session: AsyncSession,
    upload: PreparedTextUpload,
) -> StoredDocument:
    """Store the original file, document, asset, and segments atomically."""
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
            token_count=segment.token_count,
            locator={
                "line_start": segment.line_start,
                "line_end": segment.line_end,
            },
        )
        for segment in upload.segments
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
