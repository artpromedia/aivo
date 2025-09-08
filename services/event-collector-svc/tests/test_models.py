"""Test Event Collector models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models import EventBatch, LearnerEvent


class TestLearnerEvent:
    """Test LearnerEvent model validation."""

    def test_valid_event(self, sample_event: LearnerEvent):
        """Test that a valid event passes validation."""
        assert sample_event.learner_id == "test_learner_123"
        assert sample_event.course_id == "test_course_456"
        assert sample_event.lesson_id == "test_lesson_789"
        assert sample_event.event_type == "lesson_started"
        assert sample_event.event_data == {"duration": 300, "score": 85}
        assert sample_event.session_id == "test_session_abc"
        assert sample_event.metadata == {
            "device": "mobile",
            "app_version": "1.0.0",
        }

    def test_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError) as exc_info:
            LearnerEvent()

        errors = exc_info.value.errors()
        required_fields = {error["loc"][0] for error in errors}
        expected_fields = {
            "learner_id",
            "course_id",
            "lesson_id",
            "event_type",
            "event_data",
            "timestamp",
        }
        assert required_fields >= expected_fields

    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        event = LearnerEvent(
            learner_id="learner123",
            course_id="course456",
            lesson_id="lesson789",
            event_type="lesson_started",
            event_data={"key": "value"},
            timestamp="2024-01-15T10:30:00Z",
        )

        assert event.session_id is None
        assert event.metadata == {}

    def test_timestamp_parsing(self):
        """Test timestamp parsing and validation."""
        # Valid ISO timestamp
        event = LearnerEvent(
            learner_id="learner123",
            course_id="course456",
            lesson_id="lesson789",
            event_type="lesson_started",
            event_data={"key": "value"},
            timestamp="2024-01-15T10:30:00Z",
        )
        assert isinstance(event.timestamp, datetime)

        # Invalid timestamp should fail
        with pytest.raises(ValidationError):
            LearnerEvent(
                learner_id="learner123",
                course_id="course456",
                lesson_id="lesson789",
                event_type="lesson_started",
                event_data={"key": "value"},
                timestamp="invalid-timestamp",
            )

    def test_event_data_types(self):
        """Test event_data accepts various types."""
        valid_data_types = [
            {"string": "value", "number": 123, "boolean": True},
            {"nested": {"key": "value"}},
            {"list": [1, 2, 3]},
            {},
        ]

        for event_data in valid_data_types:
            event = LearnerEvent(
                learner_id="learner123",
                course_id="course456",
                lesson_id="lesson789",
                event_type="lesson_started",
                event_data=event_data,
                timestamp="2024-01-15T10:30:00Z",
            )
            assert event.event_data == event_data


class TestEventBatch:
    """Test EventBatch model validation."""

    def test_valid_batch(self, sample_events: list[LearnerEvent]):
        """Test that a valid batch passes validation."""
        batch = EventBatch(events=sample_events)
        assert len(batch.events) == 5
        assert all(isinstance(event, LearnerEvent) for event in batch.events)

    def test_empty_batch(self):
        """Test that empty batch is valid."""
        batch = EventBatch(events=[])
        assert len(batch.events) == 0

    def test_batch_metadata(self, sample_events: list[LearnerEvent]):
        """Test batch with metadata."""
        batch = EventBatch(
            events=sample_events, metadata={"source": "test", "version": "1.0"}
        )
        assert batch.metadata == {"source": "test", "version": "1.0"}
