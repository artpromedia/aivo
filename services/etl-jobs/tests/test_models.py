"""Tests for ETL jobs service."""

import pytest
from datetime import datetime, timezone

from app.models import RawEvent, ProcessingBatch, MinuteMetrics


class TestModels:
    """Test Pydantic models."""

    def test_raw_event_creation(self):
        """Test creating a RawEvent."""
        event = RawEvent(
            learner_id="learner_123",
            event_type="lesson_start",
            event_id="evt_456",
            timestamp=datetime.now(timezone.utc),
            data={"lesson_id": "lesson_001"},
            metadata={"source": "test"}
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
                timestamp=datetime.now(timezone.utc)
            )
        ]
        
        batch = ProcessingBatch(
            batch_id="batch_123",
            events=events,
            created_at=datetime.now(timezone.utc),
            partition_date="2025-09-05"
        )
        
        assert batch.batch_id == "batch_123"
        assert len(batch.events) == 1
        assert batch.status == "pending"  # Default value

    def test_minute_metrics_creation(self):
        """Test creating MinuteMetrics."""
        metrics = MinuteMetrics(
            learner_id="learner_123",
            minute_timestamp=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            partition_date="2025-09-05"
        )
        
        assert metrics.learner_id == "learner_123"
        assert metrics.total_events == 0  # Default value
        assert metrics.time_spent_seconds == 0.0  # Default value


# Integration test would go here when services are testable
@pytest.mark.asyncio
async def test_etl_processor_health():
    """Test ETL processor health check."""
    # This would be implemented when the processor can run in test mode
    pass
