"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return uuid4()


@pytest.fixture
def sample_learner_id():
    """Sample learner ID for testing."""
    return uuid4()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "problem-session-svc"
    assert "timestamp" in data
    assert "dependencies" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "Problem Session Orchestrator"
    assert data["version"] == "0.1.0"
    assert "description" in data


@patch("app.main.orchestrator.start_session")
@patch("app.main.get_db")
def test_start_session_success(
    mock_get_db, mock_start_session, client, sample_learner_id
):
    """Test successful session start."""
    # Mock database session
    mock_db = AsyncMock()
    mock_get_db.return_value.__aenter__.return_value = mock_db
    
    # Mock orchestrator response
    mock_session = AsyncMock()
    mock_session.session_id = uuid4()
    mock_session.learner_id = sample_learner_id
    mock_session.subject = "mathematics"
    mock_session.status = "active"
    mock_session.current_phase = "present"
    mock_session.created_at = "2025-09-09T10:30:00Z"
    mock_session.started_at = "2025-09-09T10:30:01Z"
    mock_session.completed_at = None
    mock_session.session_duration_minutes = 30
    mock_session.total_problems_attempted = 0
    mock_session.total_problems_correct = 0
    mock_session.average_confidence = None
    mock_session.planned_activities = None
    mock_session.current_activity_index = 0
    mock_session.canvas_width = 800
    mock_session.canvas_height = 600
    mock_session.ink_session_id = uuid4()
    mock_session.error_message = None
    
    mock_start_session.return_value = mock_session
    
    # Test request
    request_data = {
        "learner_id": str(sample_learner_id),
        "subject": "mathematics",
        "session_duration_minutes": 30,
        "canvas_width": 800,
        "canvas_height": 600
    }
    
    response = client.post("/start", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "session_id" in data
    assert data["learner_id"] == str(sample_learner_id)
    assert data["subject"] == "mathematics"
    assert data["status"] == "active"


def test_start_session_invalid_subject(client, sample_learner_id):
    """Test session start with invalid subject."""
    request_data = {
        "learner_id": str(sample_learner_id),
        "subject": "invalid_subject",
        "session_duration_minutes": 30
    }
    
    response = client.post("/start", json=request_data)
    assert response.status_code == 422  # Validation error


def test_start_session_invalid_duration(client, sample_learner_id):
    """Test session start with invalid duration."""
    request_data = {
        "learner_id": str(sample_learner_id),
        "subject": "mathematics",
        "session_duration_minutes": 200  # Too long
    }
    
    response = client.post("/start", json=request_data)
    assert response.status_code == 422  # Validation error


@patch("app.main.orchestrator.submit_ink")
@patch("app.main.get_db")
def test_submit_ink_success(
    mock_get_db, mock_submit_ink, client, sample_session_id
):
    """Test successful ink submission."""
    # Mock database session
    mock_db = AsyncMock()
    mock_get_db.return_value.__aenter__.return_value = mock_db
    
    # Mock orchestrator response
    from app.schemas import InkSubmissionResponse
    mock_response = InkSubmissionResponse(
        session_id=sample_session_id,
        page_id=uuid4(),
        recognition_job_id=uuid4(),
        status="submitted",
        message="Ink submitted successfully"
    )
    mock_submit_ink.return_value = mock_response
    
    # Test request
    request_data = {
        "session_id": str(sample_session_id),
        "page_number": 1,
        "strokes": [
            {
                "stroke_id": str(uuid4()),
                "tool_type": "pen",
                "color": "#000000",
                "width": 2.0,
                "points": [
                    {"x": 100, "y": 150, "pressure": 0.8, "timestamp": 0},
                    {"x": 110, "y": 155, "pressure": 0.9, "timestamp": 50}
                ]
            }
        ],
        "metadata": {"device": "tablet"}
    }
    
    response = client.post("/ink", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["session_id"] == str(sample_session_id)
    assert data["status"] == "submitted"
    assert "page_id" in data


def test_submit_ink_missing_strokes(client, sample_session_id):
    """Test ink submission with missing strokes."""
    request_data = {
        "session_id": str(sample_session_id),
        "page_number": 1,
        "metadata": {"device": "tablet"}
        # Missing strokes
    }
    
    response = client.post("/ink", json=request_data)
    assert response.status_code == 422  # Validation error


@patch("app.main.db.execute")
@patch("app.main.get_db")
def test_get_session_success(
    mock_get_db, mock_execute, client, sample_session_id, sample_learner_id
):
    """Test successful session retrieval."""
    # Mock database session
    mock_db = AsyncMock()
    mock_get_db.return_value.__aenter__.return_value = mock_db
    
    # Mock database query result
    mock_session = AsyncMock()
    mock_session.session_id = sample_session_id
    mock_session.learner_id = sample_learner_id
    mock_session.subject = "mathematics"
    mock_session.status = "active"
    mock_session.current_phase = "present"
    mock_session.created_at = "2025-09-09T10:30:00Z"
    mock_session.started_at = "2025-09-09T10:30:01Z"
    mock_session.completed_at = None
    mock_session.session_duration_minutes = 30
    mock_session.total_problems_attempted = 0
    mock_session.total_problems_correct = 0
    mock_session.average_confidence = None
    mock_session.planned_activities = None
    mock_session.current_activity_index = 0
    mock_session.canvas_width = 800
    mock_session.canvas_height = 600
    mock_session.ink_session_id = uuid4()
    mock_session.error_message = None
    
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_session
    mock_execute.return_value = mock_result
    
    response = client.get(f"/sessions/{sample_session_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["session_id"] == str(sample_session_id)
    assert data["learner_id"] == str(sample_learner_id)
    assert data["subject"] == "mathematics"


@patch("app.main.db.execute")
@patch("app.main.get_db")
def test_get_session_not_found(
    mock_get_db, mock_execute, client, sample_session_id
):
    """Test session retrieval when session doesn't exist."""
    # Mock database session
    mock_db = AsyncMock()
    mock_get_db.return_value.__aenter__.return_value = mock_db
    
    # Mock database query result (no session found)
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_execute.return_value = mock_result
    
    response = client.get(f"/sessions/{sample_session_id}")
    assert response.status_code == 404


@patch("app.main.orchestrator.complete_session")
@patch("app.main.get_db")
def test_complete_session_success(
    mock_get_db, mock_complete_session, client, sample_session_id
):
    """Test successful session completion."""
    # Mock database session
    mock_db = AsyncMock()
    mock_get_db.return_value.__aenter__.return_value = mock_db
    
    # Mock orchestrator method
    mock_complete_session.return_value = None
    
    response = client.post(f"/sessions/{sample_session_id}/complete")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "completed"
    assert data["session_id"] == str(sample_session_id)


def test_invalid_uuid_format(client):
    """Test endpoints with invalid UUID format."""
    invalid_uuid = "not-a-uuid"
    
    response = client.get(f"/sessions/{invalid_uuid}")
    assert response.status_code == 422  # Validation error
