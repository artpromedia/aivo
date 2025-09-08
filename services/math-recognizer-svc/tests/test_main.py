"""Tests for Math Recognizer Service."""

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
    assert "service_name" in data
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_recognize_from_ink():
    """Test direct ink recognition endpoint."""
    ink_data = {
        "strokes": [
            {
                "points": [
                    {"x": 0.0, "y": 0.0, "pressure": 1.0, "timestamp": 0},
                    {"x": 10.0, "y": 0.0, "pressure": 1.0, "timestamp": 100},
                ],
            }
        ],
        "width": 100.0,
        "height": 50.0,
    }
    
    response = client.post("/recognize", json=ink_data)
    assert response.status_code == 200
    data = response.json()
    assert "latex" in data
    assert "ast" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_grade_expression():
    """Test grading endpoint."""
    grade_request = {
        "student_expression": "x^2",
        "correct_expression": "x**2",
        "expression_type": "algebraic",
        "check_equivalence": True,
    }
    
    response = client.post("/grade", json=grade_request)
    assert response.status_code == 200
    data = response.json()
    assert "is_correct" in data
    assert "score" in data
    assert "feedback" in data


def test_recognize_session_not_found():
    """Test session recognition with invalid session ID."""
    import uuid
    
    session_id = str(uuid.uuid4())
    response = client.post(f"/recognize/{session_id}")
    
    # Should return 404 for non-existent session
    assert response.status_code == 404
