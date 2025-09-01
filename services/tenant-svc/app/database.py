"""
Database configuration and session management.
"""
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from .models import Base

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://tenant_user:tenant_pass@localhost:5432/tenant_db"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    poolclass=NullPool,  # Use NullPool for async
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """
    Create all database tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
