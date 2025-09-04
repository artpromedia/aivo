"""Test API endpoints."""

# ruff: noqa: ANN001
# pylint: disable=import-error,no-name-in-module
from unittest.mock import patch

import pytest
from app.auth import get_current_user
from app.main import app
from fastapi.testclient import TestClient


class TestLessonAPI:
    """Test lesson API endpoints."""

    @pytest.fixture
    def client(self, override_get_db):  # pylint: disable=unused-argument
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_client(self, client, test_user):
        """Create authenticated test client."""
        # Mock the get_current_user dependency
        app.dependency_overrides[get_current_user] = lambda: test_user
        yield client
        app.dependency_overrides.clear()

    @pytest.fixture
    def admin_client(self, client, admin_user):
        """Create admin authenticated test client."""
        # Mock the get_current_user dependency
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield client
        app.dependency_overrides.clear()

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "lesson-registry-svc"
        assert "version" in data

    def test_health_check(self, client):
        """Test health check endpoint."""
        with patch("app.main.cdn_service.health_check", return_value=True):
            response = client.get("/healthz")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] is True
            assert data["storage"] is True

    def test_create_lesson(self, auth_client):
        """Test creating a lesson."""
        lesson_data = {
            "title": "API Test Lesson",
            "description": "A lesson created via API",
            "subject": "Computer Science",
            "grade_band": "K-5",
            "keywords": ["programming", "basics"],
        }

        response = auth_client.post("/api/v1/lessons", json=lesson_data)
        assert response.status_code == 201

        data = response.json()
        assert data["title"] == lesson_data["title"]
        assert data["subject"] == lesson_data["subject"]
        assert data["grade_band"] == lesson_data["grade_band"]

    def test_get_lesson(self, auth_client, test_lesson):
        """Test getting a lesson."""
        response = auth_client.get(f"/api/v1/lessons/{test_lesson.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(test_lesson.id)
        assert data["title"] == test_lesson.title

    def test_get_lesson_not_found(self, auth_client):
        """Test getting a non-existent lesson."""
        fake_id = "12345678-1234-1234-1234-123456789999"
        response = auth_client.get(f"/api/v1/lessons/{fake_id}")
        assert response.status_code == 404

    def test_update_lesson(self, auth_client, test_lesson):
        """Test updating a lesson."""
        update_data = {
            "title": "Updated Lesson Title",
            "description": "Updated description",
        }

        lesson_url = f"/api/v1/lessons/{test_lesson.id}"
        response = auth_client.put(lesson_url, json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]

    def test_create_lesson_version(self, auth_client, test_lesson):
        """Test creating a lesson version."""
        version_data = {
            "content": {"slides": [{"title": "Intro", "content": "Welcome"}]},
            "summary": "Introduction version",
            "learning_objectives": ["Understand basics"],
            "duration_minutes": 30,
        }

        version_url = f"/api/v1/lessons/{test_lesson.id}/versions"
        response = auth_client.post(version_url, json=version_data)
        assert response.status_code == 201

        data = response.json()
        assert data["lesson_id"] == str(test_lesson.id)
        assert data["version_number"] == 1
        assert data["state"] == "DRAFT"
        assert data["content"] == version_data["content"]

    def test_publish_version(self, admin_client, test_version):
        """Test publishing a lesson version."""
        publish_url = f"/api/v1/versions/{test_version.id}/publish"
        response = admin_client.post(publish_url)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["version"]["state"] == "PUBLISHED"

    def test_publish_version_forbidden(self, auth_client, test_version):
        """Test publishing a version without admin permissions."""
        publish_url = f"/api/v1/versions/{test_version.id}/publish"
        response = auth_client.post(publish_url)
        assert response.status_code == 403

    def test_add_asset(self, auth_client, test_version):
        """Test adding an asset to a version."""
        asset_data = {
            "name": "test-document.pdf",
            "asset_type": "document",
            "file_path": "/documents/test-document.pdf",
            "file_size": 2048,
            "mime_type": "application/pdf",
            "alt_text": "Test document",
        }

        asset_url = f"/api/v1/versions/{test_version.id}/assets"
        response = auth_client.post(asset_url, json=asset_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == asset_data["name"]
        assert data["asset_type"] == asset_data["asset_type"]
        assert data["version_id"] == str(test_version.id)

    def test_search_lessons(self, auth_client, test_lesson):
        # pylint: disable=unused-argument
        """Test searching lessons."""
        response = auth_client.get("/api/v1/search?q=Test")
        assert response.status_code == 200

        data = response.json()
        assert "lessons" in data
        assert "total" in data
        assert "page" in data
        assert data["total"] >= 0

    def test_search_lessons_with_filters(self, auth_client, test_lesson):
        # pylint: disable=unused-argument
        """Test searching lessons with filters."""
        filter_url = "/api/v1/search?subject=Mathematics&grade_band=K-5"
        response = auth_client.get(filter_url)
        assert response.status_code == 200

        data = response.json()
        assert "lessons" in data
        # Should find our test lesson if it matches the criteria
        if data["total"] > 0:
            assert data["lessons"][0]["subject"] == "Mathematics"

    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints."""
        response = client.get("/api/v1/lessons")
        assert response.status_code == 403  # Should be forbidden without auth

        response = client.post("/api/v1/lessons", json={"title": "Test"})
        assert response.status_code == 403
