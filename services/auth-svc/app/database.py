"""
Database configuration and utilities.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://auth_user:auth_password@localhost:5432/auth_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=bool(os.getenv("DATABASE_ECHO", False)),
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base class for models
Base = declarative_base()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
