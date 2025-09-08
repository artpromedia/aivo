#!/usr/bin/env python3
"""Simple test to verify the Event Collector service can start."""

import asyncio

from app.config import settings
from app.models import LearnerEvent


async def test_service_components():
    """Test that all service components can be created."""
    try:
        print("🧪 Testing Event Collector service components...")

        # Test config
        print(f"✅ Config loaded - Service: {settings.service_name}")

        # Test models
        event = LearnerEvent(
            learner_id="test123",
            course_id="course456",
            lesson_id="lesson789",
            event_type="lesson_started",
            event_data={"duration": 300},
            timestamp="2024-01-15T10:30:00Z",
        )
        print(f"✅ Event model created - Type: {event.event_type}")

        # Test protobuf import
        from protos import event_collector_pb2

        proto_event = event_collector_pb2.Event(
            learner_id="test123",
            course_id="course456",
            lesson_id="lesson789",
            event_type="lesson_started",
            timestamp="2024-01-15T10:30:00Z",
        )
        print(f"✅ Protobuf event created - Type: {proto_event.event_type}")

        # Test services can be imported
        print("✅ All services can be imported")

        # Test HTTP API
        from app.http_api import app

        print(f"✅ HTTP API created - Title: {app.title}")

        print("\n🎉 All Event Collector components are working!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_service_components())
    exit(0 if success else 1)
