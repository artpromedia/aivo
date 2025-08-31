"""Tests for the hello-svc ping endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ping():
    """Test ping endpoint returns pong."""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == "pong"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}