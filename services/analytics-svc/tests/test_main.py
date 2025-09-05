"""Tests for Analytics Service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_summary_metrics_missing_tenant():
    """Test summary metrics endpoint without tenant_id."""
    response = client.get("/metrics/summary")
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_mastery_metrics_missing_tenant():
    """Test mastery metrics endpoint without tenant_id."""
    response = client.get("/metrics/mastery")
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_streak_metrics_missing_tenant():
    """Test streak metrics endpoint without tenant_id."""
    response = client.get("/metrics/streaks")
    assert response.status_code == 422  # Validation error
