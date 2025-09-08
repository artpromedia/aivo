"""
Test configuration and fixtures for payment service.
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment variables before importing app
os.environ["STRIPE_API_KEY"] = "sk_test_fake_key_for_testing"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_fake_secret_for_testing"

from app.database import Base, get_db
from app.main import app

# Import all models to ensure they're registered with Base
from app.services import PricingService, StripeService, SubscriptionService, WebhookService

# Test database URL - using SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Set up test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with TestSessionLocal() as session:
        yield session
        # Clean up all data after each test
        await session.rollback()

        # Delete all data from all tables
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""

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
def mock_stripe_service():
    """Create a mock Stripe service."""
    service = Mock(spec=StripeService)

    # Mock customer creation
    service.create_customer = AsyncMock(return_value=Mock(id="cus_test123"))

    # Mock price creation
    service.create_price = AsyncMock(return_value=Mock(id="price_test123"))

    # Mock checkout session creation
    service.create_checkout_session = AsyncMock(
        return_value=Mock(id="cs_test123", url="https://checkout.stripe.com/pay/cs_test123")
    )

    # Mock subscription operations
    service.retrieve_subscription = AsyncMock(
        return_value=Mock(
            id="sub_test123",
            status="active",
            current_period_start=1640995200,  # 2022-01-01
            current_period_end=1643673600,  # 2022-02-01
            trial_start=None,
            trial_end=None,
            canceled_at=None,
        )
    )

    service.cancel_subscription = AsyncMock(return_value=Mock(id="sub_test123", status="canceled"))

    return service


@pytest.fixture
def pricing_service():
    """Create a pricing service."""
    return PricingService()


@pytest.fixture
def subscription_service(mock_stripe_service):
    """Create a subscription service with mocked Stripe."""
    return SubscriptionService(mock_stripe_service)


@pytest.fixture
def webhook_service(subscription_service):
    """Create a webhook service."""
    return WebhookService(subscription_service)


# Test data fixtures
@pytest.fixture
def sample_checkout_request():
    """Sample checkout session request."""
    return {
        "tenant_id": 1,
        "plan_type": "monthly",
        "seats": 5,
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel",
        "has_sibling_discount": False,
    }


@pytest.fixture
def sample_trial_request():
    """Sample trial start request."""
    return {"tenant_id": 1, "seats": 3}


@pytest.fixture
def sample_pricing_request():
    """Sample pricing calculation request."""
    return {"plan_type": "yearly", "seats": 10, "has_sibling_discount": True}


@pytest.fixture
def sample_stripe_webhook_event():
    """Sample Stripe webhook event."""
    return {
        "id": "evt_test123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test123",
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {"tenant_id": "1", "plan_type": "monthly", "seats": "5"},
            }
        },
        "created": 1640995200,
        "livemode": False,
    }
