"""
Test configuration and fixtures for enrollment router service.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from httpx import AsyncClient, ASGITransport

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DEBUG"] = "false"

from app.main import app
from app.database import get_db, Base
from app.models import DistrictSeatAllocation, EnrollmentDecision
from app.services import PaymentService


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Create test database engine."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    TestingSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        
        # Clean up all tables for isolation
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    # Override the get_db dependency
    async def get_test_db():
        yield db_session
    
    app.dependency_overrides[get_db] = get_test_db
    
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_learner_profile():
    """Sample learner profile for testing."""
    return {
        "email": "student@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "grade_level": "3rd",
        "school": "Test Elementary"
    }


@pytest.fixture
def sample_district_context():
    """Sample district context for testing."""
    return {
        "tenant_id": 1,
        "source": "district_portal"
    }


@pytest.fixture
def sample_parent_context():
    """Sample parent context for testing."""
    return {
        "guardian_id": "guardian_123",
        "source": "parent_portal"
    }


@pytest.fixture
def mock_payment_service():
    """Mock payment service."""
    mock = Mock(spec=PaymentService)
    mock.create_checkout_session = AsyncMock(return_value={
        "session_id": "cs_test_123",
        "session_url": "https://checkout.stripe.com/pay/cs_test_123",
        "subscription_id": 1
    })
    return mock


@pytest_asyncio.fixture
async def district_allocation(db_session: AsyncSession):
    """Create test district seat allocation."""
    allocation = DistrictSeatAllocation(
        tenant_id=1,
        total_seats=100,
        reserved_seats=10,
        used_seats=20
    )
    db_session.add(allocation)
    await db_session.commit()
    await db_session.refresh(allocation)
    return allocation


@pytest_asyncio.fixture
async def enrollment_decision(db_session: AsyncSession):
    """Create test enrollment decision."""
    decision = EnrollmentDecision(
        learner_email="test@example.com",
        learner_profile={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        },
        tenant_id=1,
        context={"tenant_id": 1, "source": "test"},
        provision_source="district",
        status="completed"
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)
    return decision
