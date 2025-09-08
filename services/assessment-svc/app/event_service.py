"""
Event service for publishing assessment events.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx

from .config import settings
from .enums import EventType
from .schemas import AssessmentEvent

logger = logging.getLogger(__name__)


class EventService:
    """Service for publishing assessment events."""

    def __init__(self) -> None:
        """Initialize event service."""
        self.endpoint = settings.event_endpoint
        self.timeout = settings.event_timeout
        logger.info(f"Event service initialized with endpoint: {self.endpoint}")

    async def publish_event(
        self, event_type: EventType, session_id: str, user_id: str, data: dict[str, Any]
    ) -> bool:
        """
        Publish an assessment event.

        Args:
            event_type: Type of event to publish
            session_id: Assessment session ID
            user_id: User identifier
            data: Event-specific data

        Returns:
            True if event was published successfully, False otherwise
        """
        try:
            event = AssessmentEvent(
                event_type=event_type,
                event_id=str(uuid4()),
                timestamp=datetime.utcnow(),
                session_id=session_id,
                user_id=user_id,
                data=data,
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json=event.model_dump(),
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code in [200, 201, 202]:
                    logger.info(
                        f"Event published successfully: {event_type} for session {session_id}"
                    )
                    return True
                else:
                    logger.warning(
                        f"Event publishing failed: {response.status_code} - {response.text} "
                        f"for event {event_type} and session {session_id}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"Event publishing timeout for {event_type} and session {session_id}")
            return False
        except Exception as e:
            logger.error(f"Event publishing error for {event_type} and session {session_id}: {e}")
            return False

    async def publish_baseline_complete(
        self,
        session_id: str,
        user_id: str,
        subject: str,
        level: str,
        confidence: float,
        questions_answered: int,
        correct_answers: int,
    ) -> bool:
        """Publish BASELINE_COMPLETE event."""
        data = {
            "subject": subject,
            "level": level,
            "confidence": confidence,
            "questions_answered": questions_answered,
            "correct_answers": correct_answers,
            "accuracy": correct_answers / questions_answered if questions_answered > 0 else 0,
        }

        return await self.publish_event(EventType.BASELINE_COMPLETE, session_id, user_id, data)

    async def publish_session_started(self, session_id: str, user_id: str, subject: str) -> bool:
        """Publish SESSION_STARTED event."""
        data = {"subject": subject, "started_at": datetime.utcnow().isoformat()}

        return await self.publish_event(EventType.SESSION_STARTED, session_id, user_id, data)

    async def publish_question_answered(
        self,
        session_id: str,
        user_id: str,
        question_id: str,
        answer: Any,
        result: str,
        current_level: str,
        confidence: float,
    ) -> bool:
        """Publish QUESTION_ANSWERED event."""
        data = {
            "question_id": question_id,
            "answer": str(answer),
            "result": result,
            "current_level_estimate": current_level,
            "confidence": confidence,
        }

        return await self.publish_event(EventType.QUESTION_ANSWERED, session_id, user_id, data)


# Global event service instance
event_service = EventService()
