"""
Webhook service for sending approval events.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID
import httpx

from .models import Approval
from .schemas import WebhookPayload
from .enums import WebhookEventType
from .config import settings

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications."""
    
    def __init__(self):
        self.timeout = settings.webhook_timeout
        self.retry_attempts = settings.webhook_retry_attempts
        self.retry_delay = settings.webhook_retry_delay
    
    async def send_webhook(
        self,
        approval: Approval,
        event_type: WebhookEventType,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send webhook notification for approval event."""
        if not approval.webhook_url:
            return True
        
        # Check if this event type should be sent
        if approval.webhook_events and event_type.value not in approval.webhook_events:
            return True
        
        # Prepare payload
        data = {
            "approval_id": str(approval.id),
            "tenant_id": approval.tenant_id,
            "approval_type": approval.approval_type.value,
            "status": approval.status.value,
            "priority": approval.priority.value,
            "resource_type": approval.resource_type,
            "resource_id": approval.resource_id,
            "title": approval.title,
            "created_by": approval.created_by,
            "created_at": approval.created_at.isoformat(),
            "expires_at": approval.expires_at.isoformat(),
            "completed_at": approval.completed_at.isoformat() if approval.completed_at else None,
            "approval_progress": approval.approval_progress,
            "is_expired": approval.is_expired,
        }
        
        # Add additional data
        if additional_data:
            data.update(additional_data)
        
        payload = WebhookPayload(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            approval_id=approval.id,
            tenant_id=approval.tenant_id,
            data=data,
            callback_data=approval.callback_data
        )
        
        # Send webhook with retries
        return await self._send_with_retries(approval.webhook_url, payload.model_dump())
    
    async def _send_with_retries(self, url: str, payload: Dict[str, Any]) -> bool:
        """Send webhook with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "approval-service/1.0"
                        }
                    )
                    
                    if response.is_success:
                        logger.info(f"Webhook sent successfully to {url}")
                        return True
                    else:
                        logger.warning(
                            f"Webhook failed with status {response.status_code}: {response.text}"
                        )
                        
            except Exception as e:
                logger.error(f"Webhook attempt {attempt + 1} failed: {e}")
            
            # Wait before retry (except on last attempt)
            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay)
        
        logger.error(f"All webhook attempts failed for {url}")
        return False


# Global service instance
webhook_service = WebhookService()
