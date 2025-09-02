"""
Test configuration and fixtures for learner service.
"""
import pytest
from datetime import datetime, date
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db
from app.main import app
from app.models import Guardian, Teacher, Tenant, ProvisionSource


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
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
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    # Override the dependency
    app.dependency_overrides[get_db] = lambda: db_session
    
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_guardian(db_session: AsyncSession) -> Guardian:
    """Create a sample guardian for testing."""
    guardian = Guardian(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="555-0123"
    )
    db_session.add(guardian)
    await db_session.commit()
    await db_session.refresh(guardian)
    return guardian


@pytest.fixture
async def sample_tenant(db_session: AsyncSession) -> Tenant:
    """Create a sample tenant for testing."""
    tenant = Tenant(
        name="Springfield Elementary",
        type="school",
        contact_email="admin@springfield.edu",
        contact_phone="555-0456"
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest.fixture
async def sample_teacher(db_session: AsyncSession, sample_tenant: Tenant) -> Teacher:
    """Create a sample teacher for testing."""
    teacher = Teacher(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@springfield.edu",
        subject="Mathematics",
        tenant_id=sample_tenant.id
    )
    db_session.add(teacher)
    await db_session.commit()
    await db_session.refresh(teacher)
    return teacher


@pytest.fixture
async def second_teacher(db_session: AsyncSession, sample_tenant: Tenant) -> Teacher:
    """Create a second teacher for testing."""
    teacher = Teacher(
        first_name="Bob",
        last_name="Wilson",
        email="bob.wilson@springfield.edu",
        subject="Science",
        tenant_id=sample_tenant.id
    )
    db_session.add(teacher)
    await db_session.commit()
    await db_session.refresh(teacher)
    return teacher


@pytest.fixture
def sample_learner_data():
    """Sample learner data for testing."""
    return {
        "first_name": "Alice",
        "last_name": "Johnson",
        "email": "alice.johnson@example.com",
        "dob": "2015-06-15",  # Should be ~8 years old, grade 2-3
        "provision_source": "parent"
    }
