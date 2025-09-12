"""Database configuration and session management."""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://device_user:device_password@localhost:5432/" "device_db",
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
