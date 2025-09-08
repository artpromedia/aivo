"""Test configuration and fixtures."""

import asyncio

import pytest

from app.models import LearnerEvent


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_event() -> LearnerEvent:
    """Sample valid learner event for testing."""
    return LearnerEvent(
        learner_id="test_learner_123",
        course_id="test_course_456",
        lesson_id="test_lesson_789",
        event_type="lesson_started",
        event_data={"duration": 300, "score": 85},
        timestamp="2024-01-15T10:30:00Z",
        session_id="test_session_abc",
        metadata={"device": "mobile", "app_version": "1.0.0"},
    )


@pytest.fixture
def sample_events(sample_event: LearnerEvent) -> list[LearnerEvent]:
    """List of sample events for batch testing."""
    events = []
    for i in range(5):
        event_data = sample_event.dict()
        event_data["learner_id"] = f"learner_{i}"
        event_data["event_type"] = (
            "lesson_completed" if i % 2 else "lesson_started"
        )
        events.append(LearnerEvent(**event_data))
    return events
