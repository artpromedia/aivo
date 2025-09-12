"""
Database configuration for chat service.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://chat_user:chat_password@localhost:5432/chat_db",
)

# Create async engine with conditional pool arguments
engine_kwargs = {
    "echo": os.getenv("DATABASE_ECHO", "false").lower() == "true",
}

# Only add pool arguments for non-SQLite databases
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update(
        {
            "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
        }
    )

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create session factory
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_factory() as session:
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()
