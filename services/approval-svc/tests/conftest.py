"""
Test configuration and fixtures for the Approval Service.
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models import Base
from app.enums import ParticipantRole, ApprovalType, Priority

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine and session
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(db_session: AsyncSession):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_approval_data():
    """Sample approval data for testing."""
    return {
        "tenant_id": "test_tenant",
        "approval_type": ApprovalType.IEP_DOCUMENT,
        "priority": Priority.NORMAL,
        "resource_type": "iep_document",
        "resource_id": "iep_123",
        "title": "IEP Approval for John Doe",
        "description": "Approval required for John Doe's IEP document",
        "created_by": "teacher_123",
        "ttl_hours": 72,
        "participants": [
            {
                "user_id": "guardian_456",
                "email": "parent@example.com",
                "role": ParticipantRole.GUARDIAN,
                "display_name": "Jane Doe",
                "is_required": True
            },
            {
                "user_id": "teacher_123",
                "email": "teacher@school.edu",
                "role": ParticipantRole.TEACHER,
                "display_name": "Ms. Smith",
                "is_required": True
            }
        ],
        "webhook_url": "https://example.com/webhook",
        "webhook_events": ["approval_requested", "approval_completed"],
        "callback_data": {"source": "test"}
    }


@pytest.fixture
def sample_participant_data():
    """Sample participant data for testing."""
    return {
        "user_id": "user_789",
        "email": "user@example.com",
        "role": ParticipantRole.ADMINISTRATOR,
        "display_name": "Admin User",
        "is_required": True
    }


@pytest.fixture
def expired_approval_data(sample_approval_data):
    """Sample approval data that expires in the past."""
    data = sample_approval_data.copy()
    data["ttl_hours"] = -1  # Expired 1 hour ago
    return data
