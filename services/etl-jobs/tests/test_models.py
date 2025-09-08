"""Tests for ETL jobs service."""

from datetime import UTC, datetime

import pytest

# pylint: disable=import-error,no-name-in-module
from app.models import MinuteMetrics, ProcessingBatch, RawEvent


class TestModels:
    """Test Pydantic models."""

    def test_raw_event_creation(self):
        """Test creating a RawEvent."""
        event = RawEvent(
            learner_id="learner_123",
            event_type="lesson_start",
            event_id="evt_456",
            timestamp=datetime.now(UTC),
            data={"lesson_id": "lesson_001"},
            metadata={"source": "test"},
        )

        assert event.learner_id == "learner_123"
        assert event.event_type == "lesson_start"
        assert event.version == "1.0"  # Default value

    def test_processing_batch_creation(self):
        """Test creating a ProcessingBatch."""
        events = [
            RawEvent(
                learner_id="learner_123",
                event_type="lesson_start",
                event_id="evt_456",
                timestamp=datetime.now(UTC),
            )
        ]

        batch = ProcessingBatch(
            batch_id="batch_123",
            events=events,
            created_at=datetime.now(UTC),
            partition_date="2025-09-05",
        )

        assert batch.batch_id == "batch_123"
        assert len(batch.events) == 1
        assert batch.status == "pending"  # Default value

    def test_minute_metrics_creation(self):
        """Test creating MinuteMetrics."""
        metrics = MinuteMetrics(
            learner_id="learner_123",
            minute_timestamp=datetime.now(UTC),
            created_at=datetime.now(UTC),
            partition_date="2025-09-05",
        )

        assert metrics.learner_id == "learner_123"
        assert metrics.total_events == 0  # Default value
        assert metrics.time_spent_seconds == 0.0  # Default value


# Integration test would go here when services are testable
@pytest.mark.asyncio
async def test_etl_processor_health():
    """Test ETL processor health check."""
    # This would be implemented when the processor can run in test mode
    assert True  # Placeholder for future implementation
