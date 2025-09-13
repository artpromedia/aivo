"""Webhooks management endpoints."""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.database import get_db
from app.models import Webhook, WebhookDelivery, WebhookEvent, Tenant

logger = structlog.get_logger(__name__)
router = APIRouter()


# Pydantic schemas
class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""

    name: str = Field(..., min_length=1, max_length=255, description="Webhook name")
    description: Optional[str] = Field(None, max_length=1000, description="Webhook description")
    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., min_items=1, description="List of event types to subscribe to")
    secret: Optional[str] = Field(None, min_length=16, max_length=255, description="Webhook secret for HMAC")
    timeout_seconds: int = Field(default=30, ge=1, le=120, description="Request timeout in seconds")
    max_retries: int = Field(default=5, ge=0, le=10, description="Maximum retry attempts")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional HTTP headers")


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Webhook name")
    description: Optional[str] = Field(None, max_length=1000, description="Webhook description")
    url: Optional[HttpUrl] = Field(None, description="Webhook endpoint URL")
    events: Optional[List[str]] = Field(None, min_items=1, description="List of event types")
    secret: Optional[str] = Field(None, min_length=16, max_length=255, description="Webhook secret")
    timeout_seconds: Optional[int] = Field(None, ge=1, le=120, description="Request timeout")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="Maximum retry attempts")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional HTTP headers")
    is_active: Optional[bool] = Field(None, description="Whether webhook is active")


class WebhookResponse(BaseModel):
    """Schema for webhook response."""

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    url: str
    events: List[str]
    status: str
    is_active: bool
    timeout_seconds: int
    max_retries: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
    last_delivery_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    headers: Optional[Dict[str, str]]

    class Config:
        from_attributes = True


class WebhookList(BaseModel):
    """Schema for webhook list response."""

    webhooks: List[WebhookResponse]
    total: int
    page: int
    size: int


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response."""

    id: UUID
    webhook_id: UUID
    event_id: UUID
    status: str
    attempt_number: int
    response_status_code: Optional[int]
    response_time_ms: Optional[int]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    next_retry_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryList(BaseModel):
    """Schema for webhook delivery list response."""

    deliveries: List[WebhookDeliveryResponse]
    total: int
    page: int
    size: int


class WebhookTestRequest(BaseModel):
    """Schema for webhook test request."""

    event_type: str = Field(default="test.event", description="Test event type")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Test payload")


class WebhookTestResponse(BaseModel):
    """Schema for webhook test response."""

    success: bool
    delivery_id: UUID
    status_code: Optional[int]
    response_time_ms: Optional[int]
    error_message: Optional[str]


def generate_webhook_secret() -> str:
    """Generate a secure webhook secret."""
    return secrets.token_urlsafe(32)


def create_hmac_signature(payload: str, secret: str) -> str:
    """Create HMAC signature for webhook payload."""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


async def get_tenant_by_id(tenant_id: UUID, db: AsyncSession) -> Tenant:
    """Get tenant by ID or raise 404."""
    stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active == True)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant


@router.post("/tenants/{tenant_id}/webhooks", response_model=WebhookResponse)
async def create_webhook(
    tenant_id: UUID,
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system",  # TODO: Add proper auth
) -> WebhookResponse:
    """Create a new webhook for a tenant."""
    logger.info("Creating webhook", tenant_id=str(tenant_id), name=webhook_data.name)

    # Verify tenant exists
    tenant = await get_tenant_by_id(tenant_id, db)

    # Check webhook limit
    stmt = select(Webhook).where(Webhook.tenant_id == tenant_id)
    result = await db.execute(stmt)
    existing_webhooks = result.scalars().all()

    if len(existing_webhooks) >= tenant.max_webhooks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum number of webhooks ({tenant.max_webhooks}) exceeded"
        )

    # Generate secret if not provided
    secret = webhook_data.secret or generate_webhook_secret()

    # Create webhook record
    webhook = Webhook(
        tenant_id=tenant_id,
        name=webhook_data.name,
        description=webhook_data.description,
        url=str(webhook_data.url),
        events=webhook_data.events,
        secret=secret,
        timeout_seconds=webhook_data.timeout_seconds,
        max_retries=webhook_data.max_retries,
        headers=webhook_data.headers,
        created_by=current_user,
    )

    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    logger.info("Webhook created", webhook_id=str(webhook.id), tenant_id=str(tenant_id))

    return WebhookResponse.model_validate(webhook)


@router.get("/tenants/{tenant_id}/webhooks", response_model=WebhookList)
async def list_webhooks(
    tenant_id: UUID,
    page: int = 1,
    size: int = 50,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
) -> WebhookList:
    """List webhooks for a tenant."""
    # Verify tenant exists
    await get_tenant_by_id(tenant_id, db)

    # Build query
    conditions = [Webhook.tenant_id == tenant_id]
    if not include_inactive:
        conditions.append(Webhook.is_active == True)

    stmt = (
        select(Webhook)
        .where(and_(*conditions))
        .order_by(Webhook.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.execute(stmt)
    webhooks = result.scalars().all()

    # Get total count
    count_stmt = select(func.count(Webhook.id)).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return WebhookList(
        webhooks=[WebhookResponse.model_validate(webhook) for webhook in webhooks],
        total=total,
        page=page,
        size=size,
    )


@router.get("/tenants/{tenant_id}/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    tenant_id: UUID,
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    """Get a specific webhook."""
    stmt = select(Webhook).where(
        and_(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    return WebhookResponse.model_validate(webhook)


@router.put("/tenants/{tenant_id}/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    tenant_id: UUID,
    webhook_id: UUID,
    webhook_data: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system",  # TODO: Add proper auth
) -> WebhookResponse:
    """Update a webhook."""
    stmt = select(Webhook).where(
        and_(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Update fields
    update_data = webhook_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "url" and value:
            value = str(value)
        setattr(webhook, field, value)

    webhook.updated_by = current_user

    await db.commit()
    await db.refresh(webhook)

    logger.info("Webhook updated", webhook_id=str(webhook_id), tenant_id=str(tenant_id))

    return WebhookResponse.model_validate(webhook)


@router.delete("/tenants/{tenant_id}/webhooks/{webhook_id}")
async def delete_webhook(
    tenant_id: UUID,
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system",  # TODO: Add proper auth
) -> dict[str, str]:
    """Delete a webhook."""
    stmt = select(Webhook).where(
        and_(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    await db.delete(webhook)
    await db.commit()

    logger.info("Webhook deleted", webhook_id=str(webhook_id), tenant_id=str(tenant_id))

    return {"message": "Webhook deleted successfully"}


@router.get("/tenants/{tenant_id}/webhooks/{webhook_id}/deliveries", response_model=WebhookDeliveryList)
async def list_webhook_deliveries(
    tenant_id: UUID,
    webhook_id: UUID,
    page: int = 1,
    size: int = 50,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> WebhookDeliveryList:
    """List webhook deliveries."""
    # Verify webhook exists
    webhook_stmt = select(Webhook).where(
        and_(Webhook.id == webhook_id, Webhook.tenant_id == tenant_id)
    )
    webhook_result = await db.execute(webhook_stmt)
    webhook = webhook_result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Build query
    conditions = [WebhookDelivery.webhook_id == webhook_id]
    if status_filter:
        conditions.append(WebhookDelivery.status == status_filter)

    stmt = (
        select(WebhookDelivery)
        .where(and_(*conditions))
        .order_by(WebhookDelivery.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.execute(stmt)
    deliveries = result.scalars().all()

    # Get total count
    count_stmt = select(func.count(WebhookDelivery.id)).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return WebhookDeliveryList(
        deliveries=[WebhookDeliveryResponse.model_validate(delivery) for delivery in deliveries],
        total=total,
        page=page,
        size=size,
    )


@router.post("/tenants/{tenant_id}/webhooks/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    tenant_id: UUID,
    webhook_id: UUID,
    test_data: WebhookTestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> WebhookTestResponse:
    """Test a webhook by sending a test event."""
    # Get webhook
    stmt = select(Webhook).where(
        and_(
            Webhook.id == webhook_id,
            Webhook.tenant_id == tenant_id,
            Webhook.is_active == True,
        )
    )
    result = await db.execute(stmt)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found or inactive"
        )

    # Create test event
    event = WebhookEvent(
        event_type=test_data.event_type,
        payload=test_data.payload,
        source="webhook-test",
        tenant_id=tenant_id,
        idempotency_key=f"test-{datetime.utcnow().isoformat()}",
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    # Create delivery record
    delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event_id=event.id,
    )

    db.add(delivery)
    await db.commit()
    await db.refresh(delivery)

    # Send webhook asynchronously
    background_tasks.add_task(deliver_webhook, delivery.id)

    return WebhookTestResponse(
        success=True,
        delivery_id=delivery.id,
        status_code=None,
        response_time_ms=None,
        error_message=None,
    )


@router.post("/tenants/{tenant_id}/webhooks/{webhook_id}/deliveries/{delivery_id}/replay")
async def replay_webhook_delivery(
    tenant_id: UUID,
    webhook_id: UUID,
    delivery_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Replay a failed webhook delivery."""
    # Get delivery
    stmt = (
        select(WebhookDelivery)
        .options(selectinload(WebhookDelivery.webhook))
        .where(
            and_(
                WebhookDelivery.id == delivery_id,
                WebhookDelivery.webhook_id == webhook_id,
            )
        )
    )
    result = await db.execute(stmt)
    delivery = result.scalar_one_or_none()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    if delivery.webhook.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    # Create new delivery for replay
    new_delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event_id=delivery.event_id,
    )

    db.add(new_delivery)
    await db.commit()
    await db.refresh(new_delivery)

    # Send webhook asynchronously
    background_tasks.add_task(deliver_webhook, new_delivery.id)

    logger.info(
        "Webhook delivery replayed",
        original_delivery_id=str(delivery_id),
        new_delivery_id=str(new_delivery.id),
        webhook_id=str(webhook_id),
    )

    return {"message": "Webhook delivery replayed successfully"}


# Webhook delivery worker functions
async def deliver_webhook(delivery_id: UUID) -> None:
    """Deliver a webhook with retries and exponential backoff."""
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            # Get delivery with related data
            stmt = (
                select(WebhookDelivery)
                .options(
                    selectinload(WebhookDelivery.webhook),
                    selectinload(WebhookDelivery.event)
                )
                .where(WebhookDelivery.id == delivery_id)
            )
            result = await db.execute(stmt)
            delivery = result.scalar_one_or_none()

            if not delivery:
                logger.error("Delivery not found", delivery_id=str(delivery_id))
                return

            webhook = delivery.webhook
            event = delivery.event

            # Prepare payload
            payload = {
                "event_type": event.event_type,
                "event_version": event.event_version,
                "event_id": str(event.id),
                "tenant_id": str(event.tenant_id),
                "timestamp": event.created_at.isoformat(),
                "data": event.payload,
            }

            payload_json = json.dumps(payload, separators=(',', ':'))

            # Create HMAC signature
            signature = create_hmac_signature(payload_json, webhook.secret)

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": webhook.user_agent or f"Aivo-Webhooks/{settings.version}",
                settings.webhook_signature_header: signature,
                "X-Aivo-Event-Type": event.event_type,
                "X-Aivo-Event-ID": str(event.id),
                "X-Aivo-Delivery-ID": str(delivery.id),
                "X-Aivo-Tenant-ID": str(event.tenant_id),
            }

            # Add custom headers
            if webhook.headers:
                headers.update(webhook.headers)

            # Update delivery status
            delivery.status = "retrying"
            delivery.started_at = datetime.utcnow()
            delivery.request_headers = headers
            delivery.request_body = payload_json

            await db.commit()

            # Make HTTP request
            async with httpx.AsyncClient(timeout=webhook.timeout_seconds) as client:
                start_time = datetime.utcnow()

                try:
                    response = await client.post(
                        webhook.url,
                        content=payload_json,
                        headers=headers,
                    )

                    end_time = datetime.utcnow()
                    response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                    # Update delivery with response
                    delivery.response_status_code = response.status_code
                    delivery.response_headers = dict(response.headers)
                    delivery.response_body = response.text[:10000]  # Limit size
                    delivery.response_time_ms = response_time_ms
                    delivery.completed_at = end_time

                    # Check if successful (2xx status codes)
                    if 200 <= response.status_code < 300:
                        delivery.status = "delivered"
                        webhook.successful_deliveries += 1
                        webhook.last_success_at = end_time

                        logger.info(
                            "Webhook delivered successfully",
                            delivery_id=str(delivery_id),
                            webhook_id=str(webhook.id),
                            status_code=response.status_code,
                            response_time_ms=response_time_ms,
                        )
                    else:
                        delivery.status = "failed"
                        delivery.error_message = f"HTTP {response.status_code}: {response.text[:500]}"
                        webhook.failed_deliveries += 1
                        webhook.last_failure_at = end_time

                        logger.warning(
                            "Webhook delivery failed",
                            delivery_id=str(delivery_id),
                            webhook_id=str(webhook.id),
                            status_code=response.status_code,
                            error=delivery.error_message,
                        )

                        # Schedule retry if attempts remaining
                        await schedule_retry(delivery, webhook, db)

                except Exception as e:
                    end_time = datetime.utcnow()
                    response_time_ms = int((end_time - start_time).total_seconds() * 1000)

                    delivery.status = "failed"
                    delivery.error_message = str(e)[:1000]
                    delivery.error_type = type(e).__name__
                    delivery.response_time_ms = response_time_ms
                    delivery.completed_at = end_time
                    webhook.failed_deliveries += 1
                    webhook.last_failure_at = end_time

                    logger.error(
                        "Webhook delivery error",
                        delivery_id=str(delivery_id),
                        webhook_id=str(webhook.id),
                        error=str(e),
                        error_type=type(e).__name__,
                    )

                    # Schedule retry if attempts remaining
                    await schedule_retry(delivery, webhook, db)

            # Update webhook stats
            webhook.total_deliveries += 1
            webhook.last_delivery_at = datetime.utcnow()

            await db.commit()

        except Exception as e:
            logger.error("Error in webhook delivery worker", error=str(e), delivery_id=str(delivery_id))


async def schedule_retry(
    delivery: WebhookDelivery,
    webhook: Webhook,
    db: AsyncSession,
) -> None:
    """Schedule a retry for a failed webhook delivery."""
    if delivery.attempt_number >= webhook.max_retries:
        delivery.status = "exhausted"
        logger.info(
            "Webhook delivery exhausted",
            delivery_id=str(delivery.id),
            webhook_id=str(webhook.id),
            attempts=delivery.attempt_number,
        )
        return

    # Calculate next retry time with exponential backoff
    delay_seconds = min(
        webhook.initial_delay_seconds * (webhook.backoff_multiplier ** (delivery.attempt_number - 1)),
        webhook.max_delay_seconds
    )

    next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)

    # Create new delivery for retry
    new_delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event_id=delivery.event_id,
        attempt_number=delivery.attempt_number + 1,
        next_retry_at=next_retry_at,
    )

    db.add(new_delivery)

    logger.info(
        "Webhook retry scheduled",
        original_delivery_id=str(delivery.id),
        new_delivery_id=str(new_delivery.id),
        webhook_id=str(webhook.id),
        attempt=new_delivery.attempt_number,
        delay_seconds=delay_seconds,
        next_retry_at=next_retry_at.isoformat(),
    )
