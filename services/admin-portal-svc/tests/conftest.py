"""
Conftest for pytest configuration and shared fixtures.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.ping = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from app.config import Settings

    settings = Settings()
    settings.redis_url = "redis://localhost:6379/0"
    settings.cache_ttl = 30
    settings.tenant_service_url = "http://localhost:8001"
    settings.payment_service_url = "http://localhost:8002"
    settings.approval_service_url = "http://localhost:8003"
    settings.notification_service_url = "http://localhost:8004"
    settings.environment = "test"

    return settings
