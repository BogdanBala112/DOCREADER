"""add segment embeddings

Revision ID: 6cecdcbc3253
Revises: c4a91e7b2d08
Create Date: 2026-11-17 22:38:54.018144
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "6cecdcbc3253"
down_revision: str | Sequence[str] | None = "c4a91e7b2d08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply this schema revision."""
    op.add_column(
        "segments",
        sa.Column("embedding", Vector(768), nullable=True),
    )


def downgrade() -> None:
    """Revert this schema revision."""
    op.drop_column("segments", "embedding")
