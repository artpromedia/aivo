"""Database configuration for Edge Bundler Service."""
# flake8: noqa: E501

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

# Database URL from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/edge_bundler_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    future=True,
    pool_size=20,
    max_overflow=0,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
