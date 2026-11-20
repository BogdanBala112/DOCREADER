"""Query and remove persisted documents."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from docreader.infrastructure.models import Asset, Document, Segment


@dataclass(frozen=True)
class AssetSummary:
    """Metadata for one uploaded file version."""

    id: UUID
    version_number: int
    filename: str
    media_type: str
    byte_size: int
    segment_count: int
    created_at: datetime


@dataclass(frozen=True)
class DocumentListing:
    """A document with all its asset summaries."""

    id: UUID
    title: str
    created_at: datetime
    assets: list[AssetSummary]


def _segment_counts_subquery():
    """Subquery that counts segments per asset in one aggregation."""
    return (
        select(Segment.asset_id, func.count(Segment.id).label("cnt"))
        .group_by(Segment.asset_id)
        .subquery()
    )


async def list_documents(session: AsyncSession) -> list[DocumentListing]:
    """Return all documents ordered newest-first, each with asset summaries."""
    sq = _segment_counts_subquery()
    stmt = (
        select(Document, Asset, sq.c.cnt)
        .outerjoin(Asset, Asset.document_id == Document.id)
        .outerjoin(sq, sq.c.asset_id == Asset.id)
        .order_by(Document.created_at.desc(), Asset.version_number)
    )
    rows = (await session.execute(stmt)).all()

    doc_order: list[UUID] = []
    doc_meta: dict[UUID, tuple[str, datetime]] = {}
    doc_assets: dict[UUID, list[AssetSummary]] = {}

    for doc, asset, cnt in rows:
        if doc.id not in doc_meta:
            doc_order.append(doc.id)
            doc_meta[doc.id] = (doc.title, doc.created_at)
            doc_assets[doc.id] = []
        if asset is not None:
            doc_assets[doc.id].append(
                AssetSummary(
                    id=asset.id,
                    version_number=asset.version_number,
                    filename=asset.original_filename,
                    media_type=asset.media_type,
                    byte_size=asset.byte_size,
                    segment_count=int(cnt or 0),
                    created_at=asset.created_at,
                )
            )

    return [
        DocumentListing(
            id=doc_id,
            title=doc_meta[doc_id][0],
            created_at=doc_meta[doc_id][1],
            assets=doc_assets[doc_id],
        )
        for doc_id in doc_order
    ]


async def get_document(
    session: AsyncSession, document_id: UUID
) -> DocumentListing | None:
    """Return one document with its asset summaries, or None if not found."""
    sq = _segment_counts_subquery()
    stmt = (
        select(Document, Asset, sq.c.cnt)
        .outerjoin(Asset, Asset.document_id == Document.id)
        .outerjoin(sq, sq.c.asset_id == Asset.id)
        .where(Document.id == document_id)
        .order_by(Asset.version_number)
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return None

    doc = rows[0][0]
    assets = [
        AssetSummary(
            id=asset.id,
            version_number=asset.version_number,
            filename=asset.original_filename,
            media_type=asset.media_type,
            byte_size=asset.byte_size,
            segment_count=int(cnt or 0),
            created_at=asset.created_at,
        )
        for _, asset, cnt in rows
        if asset is not None
    ]
    return DocumentListing(
        id=doc.id, title=doc.title, created_at=doc.created_at, assets=assets
    )


async def delete_document(session: AsyncSession, document_id: UUID) -> bool:
    """Delete a document and cascade to its assets and segments.

    Returns True if the document existed and was deleted, False if not found.
    """
    exists = await session.scalar(
        select(Document.id).where(Document.id == document_id)
    )
    if exists is None:
        return False
    await session.execute(delete(Document).where(Document.id == document_id))
    await session.commit()
    return True
