"""
Test configuration and fixtures.
"""

import asyncio
import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Override the DATABASE_URL for testing before importing the app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.main import app
from app.models import Base
from app.routes import get_db_dependency

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

# Create test session factory
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session():
    """Create test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Create test client with database override."""

    # Create fresh database tables for each test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Setup database tables
    async def setup_db():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    loop.run_until_complete(setup_db())

    # Create a simple override that returns a fresh session
    async def get_test_session():
        async with TestSessionLocal() as session:
            yield session

    # Override the dependency
    app.dependency_overrides[get_db_dependency] = get_test_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clean up
        app.dependency_overrides.clear()

        async def cleanup_db():
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

        loop.run_until_complete(cleanup_db())
