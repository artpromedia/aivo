"""Database configuration and models for Device OTA & Heartbeat Service."""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import Base

# Get settings instance
settings = get_settings()

# Create async engine
DATABASE_URL_STR = str(settings.database_url)
ASYNC_URL = DATABASE_URL_STR.replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(
    ASYNC_URL,
    echo=False,
    pool_size=10,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create sync engine for migrations
sync_engine = create_engine(
    str(settings.database_url),
    echo=False,
    pool_size=10,
    pool_pre_ping=True,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all database tables (for testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
