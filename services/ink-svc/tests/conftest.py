"""Test configuration and fixtures for ink service tests."""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base


# Test database URL - using in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    test_session_local = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with test_session_local() as session:
        yield session
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def client(test_db):
    """Create test client with database dependency override."""
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_stroke_request():
    """Sample stroke request for testing."""
    return {
        "session_id": "550e8400-e29b-41d4-a716-446655440001",
        "learner_id": "550e8400-e29b-41d4-a716-446655440002",
        "subject": "mathematics",
        "page_number": 1,
        "canvas_width": 800,
        "canvas_height": 600,
        "strokes": [
            {
                "stroke_id": "550e8400-e29b-41d4-a716-446655440003",
                "tool_type": "pen",
                "color": "#000000",
                "width": 2.0,
                "points": [
                    {
                        "x": 100,
                        "y": 150,
                        "pressure": 0.8,
                        "timestamp": 0
                    },
                    {
                        "x": 105,
                        "y": 152,
                        "pressure": 0.9,
                        "timestamp": 16
                    }
                ]
            }
        ],
        "metadata": {"device": "tablet", "app_version": "1.0.0"}
    }
