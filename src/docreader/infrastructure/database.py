"""SQLAlchemy engine and database health utilities."""

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_database_engine(database_url: URL) -> AsyncEngine:
    """Create the process-wide asynchronous database engine."""
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
    )


async def verify_database_connection(engine: AsyncEngine) -> None:
    """Raise when the database cannot execute a minimal query."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
