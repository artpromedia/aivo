"""Tests for Game Generation Service API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models import SubjectType


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "game-gen-svc"


def test_generate_manifest_success(client: TestClient):
    """Test successful manifest generation."""
    request_data = {
        "learner_id": "test-learner-123",
        "subject": "math",
        "grade": 3,
        "duration_minutes": 10,
        "accessibility": {
            "reduced_motion": False,
            "high_contrast": False,
            "large_text": False,
            "audio_cues": True,
            "simplified_ui": False,
            "color_blind_friendly": False
        }
    }
    
    response = client.post("/manifest", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "manifest" in data
    assert "generation_time_ms" in data
    assert data["learner_id"] == "test-learner-123"
    
    manifest = data["manifest"]
    assert manifest["subject"] == "math"
    assert manifest["grade"] == 3
    assert manifest["duration_minutes"] == 10
    assert len(manifest["scenes"]) > 0


def test_generate_manifest_accessibility(client: TestClient):
    """Test manifest generation with accessibility features."""
    request_data = {
        "learner_id": "test-learner-a11y",
        "subject": "english",
        "grade": 2,
        "duration_minutes": 15,
        "accessibility": {
            "reduced_motion": True,
            "high_contrast": True,
            "large_text": True,
            "audio_cues": True,
            "simplified_ui": True,
            "color_blind_friendly": True
        }
    }
    
    response = client.post("/manifest", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    manifest = data["manifest"]
    
    # Verify accessibility settings are preserved
    accessibility = manifest["accessibility"]
    assert accessibility["reduced_motion"] is True
    assert accessibility["high_contrast"] is True
    assert accessibility["large_text"] is True
    assert accessibility["audio_cues"] is True


def test_generate_manifest_validation_error(client: TestClient):
    """Test manifest generation with invalid data."""
    request_data = {
        "learner_id": "test-learner-invalid",
        "subject": "invalid_subject",
        "grade": -1,
        "duration_minutes": 0
    }
    
    response = client.post("/manifest", json=request_data)
    assert response.status_code == 422  # Validation error


def test_cache_stats(client: TestClient):
    """Test cache statistics endpoint."""
    response = client.get("/cache/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "hit_count" in data
    assert "miss_count" in data
    assert "hit_rate" in data
    assert "size_bytes" in data


def test_performance_stats(client: TestClient):
    """Test performance statistics endpoint."""
    response = client.get("/performance")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_generations" in data
    assert "average_generation_time_ms" in data
    assert "target_time_ms" in data
    assert "cache_hit_rate" in data


def test_available_games(client: TestClient):
    """Test available games endpoint."""
    response = client.get("/subjects/math/games?grade=3")
    assert response.status_code == 200
    
    data = response.json()
    assert data["subject"] == "math"
    assert data["grade"] == 3
    assert "available_games" in data
    assert "accessibility_features" in data
    assert len(data["available_games"]) > 0


def test_warm_cache(client: TestClient):
    """Test cache warming endpoint."""
    response = client.post("/cache/warm?subject=math&grade=3")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "math" in data["message"]
    assert "grade 3" in data["message"]


def test_clear_cache(client: TestClient):
    """Test cache clearing endpoint."""
    response = client.delete("/cache/clear")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "cleared" in data["message"].lower()


@pytest.mark.parametrize("subject,grade", [
    ("math", 1),
    ("english", 3),
    ("science", 5),
    ("art", 2),
    ("music", 4)
])
def test_generate_manifest_all_subjects(client: TestClient, subject: str, grade: int):
    """Test manifest generation for all supported subjects."""
    request_data = {
        "learner_id": f"test-learner-{subject}",
        "subject": subject,
        "grade": grade,
        "duration_minutes": 10,
        "accessibility": {}
    }
    
    response = client.post("/manifest", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    manifest = data["manifest"]
    assert manifest["subject"] == subject
    assert manifest["grade"] == grade


def test_performance_target_met(client: TestClient):
    """Test that generation meets performance targets."""
    request_data = {
        "learner_id": "test-performance",
        "subject": "math",
        "grade": 3,
        "duration_minutes": 5,
        "accessibility": {}
    }
    
    response = client.post("/manifest", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    # Should meet ≤1000ms target
    assert data["generation_time_ms"] <= 1000
