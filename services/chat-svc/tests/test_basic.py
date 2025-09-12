"""
Basic tests for chat service.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base

# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def get_test_db():
    """Override database dependency for tests."""
    async with test_session_factory() as session:
        yield session


# Override the dependency
app.dependency_overrides[get_db] = get_test_db


@pytest.fixture
async def setup_database():
    """Set up test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "chat-svc"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Chat Service API"
        assert data["service"] == "chat-svc"


def test_sync_client():
    """Test with synchronous client."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200

    response = client.get("/")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])
