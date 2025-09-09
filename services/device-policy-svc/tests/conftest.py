"""Test configuration and fixtures."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Policy, PolicyStatus, PolicyType
from app.services import AllowlistService, PolicyService

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture
async def db_session():
    """Create test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def policy_service():
    """Policy service instance."""
    return PolicyService()


@pytest.fixture
def allowlist_service():
    """Allowlist service instance."""
    return AllowlistService()


@pytest.fixture
def sample_policy():
    """Sample policy for testing."""
    return Policy(
        policy_id=uuid4(),
        name="Test Kiosk Policy",
        description="Test policy for kiosk mode",
        policy_type=PolicyType.KIOSK,
        status=PolicyStatus.DRAFT,
        config={
            "mode": "single_app",
            "apps": [
                {
                    "package_name": "com.aivo.study",
                    "app_name": "Aivo Study",
                    "auto_launch": True,
                    "allow_exit": False,
                    "fullscreen": True,
                }
            ],
        },
        version=1,
        checksum="test-checksum",
        priority=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
