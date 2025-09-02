"""
Test configuration and fixtures for private brain orchestrator tests.
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models import Base


# Test database engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

# Test session factory
TestSessionLocal = async_sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def get_test_db() -> AsyncSession:
    """Override database dependency for testing."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def app(db_session):
    """Create FastAPI app for testing."""
    from app.main import app
    from app.database import get_db
    
    # Override the database dependency
    app.dependency_overrides[get_db] = lambda: db_session
    yield app
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    """Create test client"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_learner_id():
    """Sample learner ID for testing."""
    return 12345


@pytest.fixture
def sample_request_data(sample_learner_id):
    """Sample private brain request data."""
    return {
        "learner_id": sample_learner_id,
        "request_source": "learner-svc",
        "request_id": "test-request-123"
    }
