"""Test configuration for Game Generation Service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import SubjectType, AccessibilitySettings


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_manifest_request():
    """Sample manifest request for testing."""
    return {
        "learner_id": "test-learner-123",
        "subject": SubjectType.MATH,
        "grade": 3,
        "duration_minutes": 10,
        "accessibility": AccessibilitySettings()
    }


@pytest.fixture
def accessibility_request():
    """Accessibility-focused manifest request."""
    return {
        "learner_id": "test-learner-a11y",
        "subject": SubjectType.ENGLISH,
        "grade": 2,
        "duration_minutes": 15,
        "accessibility": AccessibilitySettings(
            reduced_motion=True,
            high_contrast=True,
            large_text=True,
            audio_cues=True
        )
    }
