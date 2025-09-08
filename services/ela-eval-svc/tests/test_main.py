"""Tests for ELA evaluator service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import EvaluationRequest, GradeBand, RubricCriterion

client = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service_name"] == "ela-eval-svc"


def test_root_endpoint() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data


def test_evaluate_submission() -> None:
    """Test submission evaluation endpoint."""
    request_data = {
        "prompt": "Write about your favorite season and why you like it.",
        "submission": (
            "I love summer because it's warm and I can go swimming. "
            "The sun is bright and I can play outside with my friends. "
            "We have barbecues and go to the beach."
        ),
        "grade_band": "3-5",
        "criteria": ["ideas_and_content", "organization", "voice"],
    }

    response = client.post("/evaluate", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "evaluation_id" in data
    assert "scores" in data
    assert "overall_score" in data
    assert data["grade_band"] == "3-5"
    assert len(data["scores"]) == 3


def test_evaluate_submission_validation_error() -> None:
    """Test submission evaluation with validation error."""
    request_data = {
        "prompt": "Write about something.",
        "submission": "",  # Empty submission should fail
        "grade_band": "3-5",
    }

    response = client.post("/evaluate", json=request_data)
    assert response.status_code == 422  # Validation error


def test_evaluate_submission_too_long() -> None:
    """Test submission that's too long."""
    request_data = {
        "prompt": "Write about something.",
        "submission": "x" * 15000,  # Exceeds max length
        "grade_band": "3-5",
    }

    response = client.post("/evaluate", json=request_data)
    assert response.status_code == 400


def test_evaluate_submission_invalid_grade_band() -> None:
    """Test submission with invalid grade band."""
    request_data = {
        "prompt": "Write about something.",
        "submission": "This is a test submission.",
        "grade_band": "invalid-grade",
    }

    response = client.post("/evaluate", json=request_data)
    assert response.status_code == 422  # Validation error


def test_get_evaluation_history() -> None:
    """Test evaluation history endpoint."""
    response = client.get("/evaluations")
    assert response.status_code == 200
    
    data = response.json()
    assert "evaluations" in data
    assert "total_count" in data
    assert "has_more" in data


def test_get_evaluation_by_id_not_found() -> None:
    """Test getting evaluation by ID that doesn't exist."""
    test_id = "123e4567-e89b-12d3-a456-426614174000"
    response = client.get(f"/evaluations/{test_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_evaluation_request_validation() -> None:
    """Test evaluation request validation."""
    # Test valid request
    request = EvaluationRequest(
        prompt="Write about your favorite book.",
        submission="My favorite book is Harry Potter.",
        grade_band=GradeBand.GRADES_3_5,
    )
    assert request.submission == "My favorite book is Harry Potter."
    assert request.grade_band == GradeBand.GRADES_3_5

    # Test default criteria
    assert len(request.criteria) == 6  # All criteria by default

    # Test specific criteria
    request_with_criteria = EvaluationRequest(
        prompt="Write about your favorite book.",
        submission="My favorite book is Harry Potter.",
        grade_band=GradeBand.GRADES_3_5,
        criteria=[RubricCriterion.IDEAS_AND_CONTENT, RubricCriterion.VOICE],
    )
    assert len(request_with_criteria.criteria) == 2
