"""Persistence models for source files and normalized text segments."""

from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from docreader.infrastructure.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Logical document that can have multiple uploaded file versions."""

    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An immutable uploaded file representing one document version."""

    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint("version_number > 0", name="positive_version_number"),
        CheckConstraint("byte_size >= 0", name="non_negative_byte_size"),
        CheckConstraint(
            "octet_length(content) = byte_size",
            name="content_matches_byte_size",
        ),
        CheckConstraint("char_length(sha256) = 64", name="valid_sha256_length"),
        UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_assets_document_version",
        ),
        UniqueConstraint(
            "document_id",
            "sha256",
            name="uq_assets_document_sha256",
        ),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(127), nullable=False)
    file_content: Mapped[bytes] = mapped_column(
        "content",
        LargeBinary,
        nullable=False,
    )
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    document: Mapped[Document] = relationship(back_populates="assets")
    segments: Mapped[list["Segment"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Segment.position",
    )


class Segment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Normalized retrievable text extracted from an asset."""

    __tablename__ = "segments"
    __table_args__ = (
        CheckConstraint("position >= 0", name="non_negative_position"),
        CheckConstraint(
            "token_count IS NULL OR token_count >= 0",
            name="non_negative_token_count",
        ),
        CheckConstraint("char_length(content) > 0", name="non_empty_content"),
        UniqueConstraint(
            "asset_id",
            "position",
            name="uq_segments_asset_position",
        ),
    )

    asset_id: Mapped[UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    locator: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    segment_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    asset: Mapped[Asset] = relationship(back_populates="segments")
