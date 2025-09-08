"""Tests for ink capture API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_submit_strokes_success(
    client: TestClient, sample_stroke_request
):
    """Test successful stroke submission."""
    response = client.post("/strokes", json=sample_stroke_request)
    assert response.status_code == 201

    data = response.json()
    assert "session_id" in data
    assert "page_id" in data
    assert "s3_key" in data
    assert data["stroke_count"] == 1
    assert data["session_id"] == sample_stroke_request["session_id"]


@pytest.mark.asyncio
async def test_submit_strokes_validation_error(client: TestClient):
    """Test stroke submission with validation errors."""
    invalid_request = {
        "session_id": "invalid-uuid",
        "learner_id": "550e8400-e29b-41d4-a716-446655440002",
        "subject": "",  # Empty subject should fail validation
        "strokes": [],  # Empty strokes should fail validation
        "canvas_width": 800,
        "canvas_height": 600,
    }

    response = client.post("/strokes", json=invalid_request)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_submit_strokes_too_many_strokes(client: TestClient):
    """Test stroke submission with too many strokes."""
    # Create request with excessive strokes
    stroke_request = {
        "session_id": "550e8400-e29b-41d4-a716-446655440001",
        "learner_id": "550e8400-e29b-41d4-a716-446655440002",
        "subject": "mathematics",
        "page_number": 1,
        "canvas_width": 800,
        "canvas_height": 600,
        "strokes": [
            {
                "stroke_id": f"550e8400-e29b-41d4-a716-44665544{i:04d}",
                "tool_type": "pen",
                "color": "#000000",
                "width": 2.0,
                "points": [
                    {"x": 100, "y": 150, "pressure": 0.8, "timestamp": 0}
                ]
            }
            for i in range(1001)  # Exceeds max limit
        ]
    }

    response = client.post("/strokes", json=stroke_request)
    assert response.status_code == 400


def test_get_session_status_not_found(client: TestClient):
    """Test getting status for non-existent session."""
    session_id = "550e8400-e29b-41d4-a716-446655440099"
    response = client.get(f"/sessions/{session_id}/status")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_status_success(
    client: TestClient, sample_stroke_request
):
    """Test getting session status after creating session."""
    # First create a session by submitting strokes
    client.post("/strokes", json=sample_stroke_request)

    # Then get session status
    session_id = sample_stroke_request["session_id"]
    response = client.get(f"/sessions/{session_id}/status")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == session_id
    assert data["learner_id"] == sample_stroke_request["learner_id"]
    assert data["subject"] == sample_stroke_request["subject"]
    assert data["status"] == "active"
    assert data["page_count"] == 1


def test_get_session_status_invalid_uuid(client: TestClient):
    """Test getting session status with invalid UUID."""
    response = client.get("/sessions/invalid-uuid/status")
    assert response.status_code == 400
