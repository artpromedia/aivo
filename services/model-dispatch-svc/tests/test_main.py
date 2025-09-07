"""Tests for main API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import GradeBand, LLMProvider, Region, SubjectType


class TestMainAPI:
    """Test main API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "model-dispatch-svc"
        assert "timestamp" in data

    def test_policy_request(self, client):
        """Test policy request endpoint."""
        request_data = {
            "subject": SubjectType.MATH.value,
            "grade_band": GradeBand.K_2.value,
            "region": Region.US_WEST.value,
            "student_id": "test_student",
            "teacher_id": "test_teacher",
        }

        response = client.post("/policy", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "endpoint" in data
        assert "model_name" in data
        assert data["region"] == Region.US_WEST.value

    def test_policy_request_invalid_subject(self, client):
        """Test policy request with invalid subject."""
        request_data = {
            "subject": "INVALID_SUBJECT",
            "grade_band": GradeBand.K_2.value,
            "region": Region.US_WEST.value,
            "student_id": "test_student",
            "teacher_id": "test_teacher",
        }

        response = client.post("/policy", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_teacher_override(self, client):
        """Test teacher override creation."""
        override_data = {
            "teacher_id": "test_teacher",
            "preferred_provider": LLMProvider.OPENAI.value,
            "subject": SubjectType.MATH.value,
            "grade_band": GradeBand.K_2.value,
            "duration_hours": 24,
            "reason": "Testing override functionality",
        }

        response = client.post("/override", json=override_data)
        assert response.status_code == 200
        data = response.json()
        assert "override_id" in data
        assert data["applied"] is True
        assert "expires_at" in data

    def test_stats_endpoint(self, client):
        """Test statistics endpoint."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "cache_hits" in data
        assert "cache_misses" in data
        assert "provider_distribution" in data

    def test_cache_clear(self, client):
        """Test cache clear endpoint."""
        response = client.post("/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_cache_invalidate_subject(self, client):
        """Test subject cache invalidation."""
        subject = SubjectType.MATH.value
        response = client.post(f"/cache/invalidate/subject/{subject}")
        assert response.status_code == 200
        data = response.json()
        assert subject in data["message"]

    def test_config_reload(self, client):
        """Test configuration reload."""
        response = client.post("/config/reload")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "timestamp" in data
