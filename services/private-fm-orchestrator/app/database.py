"""
Database configuration for private brain orchestrator.
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from .models import Base

# Database URL - use SQLite for development, PostgreSQL for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./private_brain_orchestrator.db")

# For testing, use in-memory SQLite
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
