"""Test configuration for Game Generation Service."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
    from app.models import AccessibilitySettings, SubjectType
except ImportError:
    # Add the project root to Python path for proper imports
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from app.main import app
    from app.models import AccessibilitySettings, SubjectType


@pytest.fixture
def client() -> TestClient:
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def sample_manifest_request() -> dict:
    """Sample manifest request for testing."""
    return {
        "learner_id": "test-learner-123",
        "subject": SubjectType.MATH,
        "grade": 3,
        "duration_minutes": 10,
        "accessibility": AccessibilitySettings(),
    }


@pytest.fixture
def accessibility_request() -> dict:
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
        ),
    }
