"""
Database configuration and connection management.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database engine configuration
engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    poolclass=NullPool if settings.environment == "test" else None,
    future=True
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)

# Base class for ORM models
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

Base = declarative_base(metadata=metadata)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from . import models  # noqa: F401

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def drop_db() -> None:
    """Drop all database tables. Use with caution!"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


class DatabaseManager:
    """Database connection and transaction management."""

    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal

    async def create_session(self) -> AsyncSession:
        """Create a new database session."""
        return self.session_factory()

    async def execute_in_transaction(self, operation):
        """Execute operation within a database transaction."""
        async with self.session_factory() as session:
            try:
                result = await operation(session)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def close(self):
        """Close database engine."""
        await self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()
