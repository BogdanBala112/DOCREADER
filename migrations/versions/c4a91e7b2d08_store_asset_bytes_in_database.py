"""store asset bytes in database

Revision ID: c4a91e7b2d08
Revises: 89986331c183
Create Date: 2026-11-14 14:35:00.000000
"""

from collections.abc import Sequence
from pathlib import Path
from urllib.parse import unquote, urlparse

import sqlalchemy as sa
from alembic import op

revision: str = "c4a91e7b2d08"
down_revision: str | Sequence[str] | None = "89986331c183"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Move original uploaded files from disk into the assets table."""
    op.add_column("assets", sa.Column("content", sa.LargeBinary(), nullable=True))
    connection = op.get_bind()
    assets = connection.execute(
        sa.text("SELECT id, storage_uri, byte_size FROM assets")
    ).all()

    for asset in assets:
        data = _read_stored_file(asset.storage_uri)
        if len(data) != asset.byte_size:
            raise RuntimeError(
                f"File size for asset {asset.id} does not match byte_size"
            )
        connection.execute(
            sa.text("UPDATE assets SET content = :content WHERE id = :asset_id"),
            {"content": data, "asset_id": asset.id},
        )

    op.alter_column("assets", "content", nullable=False)
    op.create_check_constraint(
        op.f("ck_assets_content_matches_byte_size"),
        "assets",
        "octet_length(content) = byte_size",
    )
    op.drop_column("assets", "storage_uri")


def downgrade() -> None:
    """Restore the filesystem location column without recreating removed files."""
    op.add_column("assets", sa.Column("storage_uri", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE assets SET storage_uri = 'file://removed/' || id::text "
            "WHERE storage_uri IS NULL"
        )
    )
    op.alter_column("assets", "storage_uri", nullable=False)
    op.drop_constraint(
        op.f("ck_assets_content_matches_byte_size"),
        "assets",
        type_="check",
    )
    op.drop_column("assets", "content")


def _read_stored_file(storage_uri: str) -> bytes:
    parsed = urlparse(storage_uri)
    if parsed.scheme != "file":
        raise RuntimeError(f"Unsupported storage URI: {storage_uri}")
    return Path(unquote(parsed.path)).read_bytes()
