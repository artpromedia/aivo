"""
Database connection and session management for ink capture service.

This module provides async database connectivity, session management,
and table initialization utilities.
"""
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import settings
from .models import Base

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide database sessions.

    Yields an async database session for dependency injection in FastAPI
    endpoints.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def drop_tables() -> None:
    """Drop all database tables (for testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped successfully")


async def health_check() -> dict[str, str]:
    """
    Check database connectivity for health endpoints.

    Returns a dictionary with database status information.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return {"database": "healthy"}
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        logger.error("Database health check failed: %s", str(e))
        return {"database": "unhealthy", "error": str(e)}
