"""
Event publishing service for IEP Service.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
import httpx

from .config import settings
from .enums import EventType

logger = logging.getLogger(__name__)


class EventService:
    """
    Handles event publishing for IEP service.
    """
    
    def __init__(self):
        """Initialize the event service."""
        self.endpoint = settings.event_endpoint
        self.timeout = settings.event_timeout
    
    async def publish_event(
        self,
        event_type: EventType,
        resource_id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Publish an event to the event service.
        """
        try:
            event_payload = {
                "event_type": event_type.value,
                "event_id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "service": "iep-svc",
                "resource_type": "iep_document",
                "resource_id": resource_id,
                "user_id": user_id,
                "data": data
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json=event_payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                logger.info(f"Published event {event_type.value} for resource {resource_id}")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error publishing event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            return False
    
    async def publish_iep_created(
        self,
        iep_id: str,
        student_id: str,
        created_by: str,
        student_name: str,
        school_year: str
    ) -> bool:
        """Publish IEP_CREATED event."""
        return await self.publish_event(
            event_type=EventType.IEP_CREATED,
            resource_id=iep_id,
            user_id=created_by,
            data={
                "student_id": student_id,
                "student_name": student_name,
                "school_year": school_year,
                "status": "draft"
            }
        )
    
    async def publish_iep_updated(
        self,
        iep_id: str,
        student_id: str,
        status: str,
        updated_by: str,
        changes: List[str]
    ) -> bool:
        """Publish IEP_UPDATED event."""
        return await self.publish_event(
            event_type=EventType.IEP_UPDATED,
            resource_id=iep_id,
            user_id=updated_by,
            data={
                "student_id": student_id,
                "status": status,
                "changes": changes,
                "updated_at": datetime.utcnow().isoformat()
            }
        )
    
    async def publish_iep_submitted(
        self,
        iep_id: str,
        student_id: str,
        submitted_by: str,
        approval_request_id: str
    ) -> bool:
        """Publish IEP_SUBMITTED event."""
        return await self.publish_event(
            event_type=EventType.IEP_SUBMITTED,
            resource_id=iep_id,
            user_id=submitted_by,
            data={
                "student_id": student_id,
                "approval_request_id": approval_request_id,
                "status": "pending_approval"
            }
        )
    
    async def publish_iep_approved(
        self,
        iep_id: str,
        student_id: str,
        approved_by: List[str],
        approval_count: int
    ) -> bool:
        """Publish IEP_APPROVED event."""
        return await self.publish_event(
            event_type=EventType.IEP_APPROVED,
            resource_id=iep_id,
            data={
                "student_id": student_id,
                "approved_by": approved_by,
                "approval_count": approval_count,
                "status": "approved"
            }
        )
    
    async def publish_goal_added(
        self,
        iep_id: str,
        goal_id: str,
        student_id: str,
        added_by: str,
        goal_type: str
    ) -> bool:
        """Publish GOAL_ADDED event."""
        return await self.publish_event(
            event_type=EventType.GOAL_ADDED,
            resource_id=iep_id,
            user_id=added_by,
            data={
                "student_id": student_id,
                "goal_id": goal_id,
                "goal_type": goal_type
            }
        )
    
    async def publish_goal_updated(
        self,
        iep_id: str,
        goal_id: str,
        student_id: str,
        updated_by: str,
        changes: List[str]
    ) -> bool:
        """Publish GOAL_UPDATED event."""
        return await self.publish_event(
            event_type=EventType.GOAL_UPDATED,
            resource_id=iep_id,
            user_id=updated_by,
            data={
                "student_id": student_id,
                "goal_id": goal_id,
                "changes": changes
            }
        )
    
    async def publish_accommodation_added(
        self,
        iep_id: str,
        accommodation_id: str,
        student_id: str,
        added_by: str,
        accommodation_type: str
    ) -> bool:
        """Publish ACCOMMODATION_ADDED event."""
        return await self.publish_event(
            event_type=EventType.ACCOMMODATION_ADDED,
            resource_id=iep_id,
            user_id=added_by,
            data={
                "student_id": student_id,
                "accommodation_id": accommodation_id,
                "accommodation_type": accommodation_type
            }
        )


# Global event service instance
event_service = EventService()
