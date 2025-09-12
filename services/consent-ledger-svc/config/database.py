"""
Database configuration and connection management.

Async SQLAlchemy setup with connection pooling and health checks.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .settings import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class DatabaseManager:
    """Database connection and session management."""

    def __init__(self, database_url: str = None):
        """Initialize database manager."""
        settings = get_settings()
        self.database_url = database_url or settings.DATABASE_URL

        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.DATABASE_ECHO,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1 hour
        )

        # Create session factory
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def create_tables(self):
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        return self.SessionLocal()


# Global database manager instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Provides an async database session with automatic cleanup.
    """
    db_manager = get_database_manager()
    session = db_manager.get_session()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    # Only applies to SQLite
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


# Database health check helper
async def is_database_healthy() -> bool:
    """Check if database is healthy and responsive."""
    try:
        db_manager = get_database_manager()
        return await db_manager.health_check()
    except Exception:
        return False


# Database initialization helper
async def init_database():
    """Initialize database tables and connections."""
    db_manager = get_database_manager()
    await db_manager.create_tables()


# Database cleanup helper
async def cleanup_database():
    """Clean up database connections."""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.close()
        _db_manager = None
