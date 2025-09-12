"""Database configuration and session management."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://evidence_user:evidence_pass@localhost:5432/evidence_db",
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        Database session
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create database tables."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def reset_database():
    """Reset database by dropping and recreating tables."""
    await drop_tables()
    await create_tables()
