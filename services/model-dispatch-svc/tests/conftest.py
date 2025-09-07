"""Test configuration for Model Dispatch Policy Service."""

import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.services.cache_service import cache_service
from app.services.policy_engine import policy_engine


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def setup_services():
    """Setup test services."""
    await cache_service.connect()
    await policy_engine.initialize()
    yield
    await cache_service.disconnect()
