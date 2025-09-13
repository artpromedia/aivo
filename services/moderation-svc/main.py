"""Content Moderation Service for Trust & Safety.

This service provides content moderation queue management, decision processing,
and audit trail for flagged content including OCR uploads, chats, and ink images.

Features:
- Moderation queue with priority filtering
- Decision processing (approve, soft-block, hard-block)
- Comprehensive audit logging
- Integration with learner pipeline
- Content flagging and appeals workflow
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog
from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, desc, func, update

from models import (
    Base,
    ModerationQueueItem,
    ModerationDecision,
    AuditLog,
    ContentType,
    ModerationStatus,
    DecisionType,
    SeverityLevel
)
from schemas import (
    QueueItemResponse,
    QueueListResponse,
    ModerationDecisionRequest,
    ModerationDecisionResponse,
    QueueStatsResponse,
    AuditLogResponse
)
from services.moderation_service import ModerationService
from services.audit_service import AuditService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Database configuration
DATABASE_URL = "postgresql+asyncpg://moderation_user:moderation_pass@localhost:5432/moderation_db"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Content Moderation Service",
    description="Trust & Safety content moderation queue and decision system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Dependency for moderation service
async def get_moderation_service(db: AsyncSession = Depends(get_db)) -> ModerationService:
    return ModerationService(db)

# Dependency for audit service
async def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Content Moderation Service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    await engine.dispose()
    logger.info("Content Moderation Service stopped")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}

# Moderation Queue Endpoints

@app.get("/moderation/queue", response_model=QueueListResponse)
@limiter.limit("100/minute")
async def get_moderation_queue(
    request,
    status_filter: Optional[ModerationStatus] = Query(None, description="Filter by moderation status"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    severity: Optional[SeverityLevel] = Query(None, description="Filter by severity level"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Get the moderation queue with filtering and pagination."""
    try:
        result = await moderation_service.get_queue_items(
            status_filter=status_filter,
            content_type=content_type,
            severity=severity,
            limit=limit,
            offset=offset
        )

        logger.info(
            "Moderation queue retrieved",
            filters={
                "status": status_filter,
                "content_type": content_type,
                "severity": severity,
                "limit": limit,
                "offset": offset
            },
            count=len(result["items"])
        )

        return result
    except Exception as e:
        logger.error("Failed to retrieve moderation queue", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve moderation queue"
        )

@app.get("/moderation/queue/{item_id}", response_model=QueueItemResponse)
@limiter.limit("200/minute")
async def get_queue_item(
    request,
    item_id: str,
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Get a specific moderation queue item by ID."""
    try:
        item = await moderation_service.get_queue_item(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moderation queue item not found"
            )

        logger.info("Queue item retrieved", item_id=item_id)
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve queue item", item_id=item_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue item"
        )

@app.post("/moderation/{item_id}/decision", response_model=ModerationDecisionResponse)
@limiter.limit("50/minute")
async def make_moderation_decision(
    request,
    item_id: str,
    decision_data: ModerationDecisionRequest,
    background_tasks: BackgroundTasks,
    moderation_service: ModerationService = Depends(get_moderation_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Make a moderation decision on a queue item."""
    try:
        # Process the moderation decision
        decision = await moderation_service.make_decision(
            item_id=item_id,
            decision_type=decision_data.decision_type,
            reason=decision_data.reason,
            notes=decision_data.notes,
            moderator_id=decision_data.moderator_id,
            expires_at=decision_data.expires_at
        )

        # Schedule background task for audit logging
        background_tasks.add_task(
            audit_service.log_moderation_decision,
            decision_id=decision["id"],
            item_id=item_id,
            decision_type=decision_data.decision_type,
            moderator_id=decision_data.moderator_id,
            reason=decision_data.reason
        )

        # Schedule background task for pipeline integration
        background_tasks.add_task(
            moderation_service.update_learner_pipeline,
            item_id=item_id,
            decision_type=decision_data.decision_type
        )

        logger.info(
            "Moderation decision made",
            item_id=item_id,
            decision_id=decision["id"],
            decision_type=decision_data.decision_type,
            moderator_id=decision_data.moderator_id
        )

        return decision
    except ValueError as e:
        logger.warning("Invalid moderation decision", item_id=item_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to make moderation decision", item_id=item_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to make moderation decision"
        )

@app.get("/moderation/stats", response_model=QueueStatsResponse)
@limiter.limit("20/minute")
async def get_moderation_stats(
    request,
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Get moderation queue statistics."""
    try:
        stats = await moderation_service.get_queue_stats(days=days)
        logger.info("Moderation stats retrieved", days=days)
        return stats
    except Exception as e:
        logger.error("Failed to retrieve moderation stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve moderation stats"
        )

@app.get("/moderation/audit", response_model=List[AuditLogResponse])
@limiter.limit("50/minute")
async def get_audit_logs(
    request,
    item_id: Optional[str] = Query(None, description="Filter by item ID"),
    moderator_id: Optional[str] = Query(None, description="Filter by moderator ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Get audit logs for moderation actions."""
    try:
        logs = await audit_service.get_audit_logs(
            item_id=item_id,
            moderator_id=moderator_id,
            action=action,
            limit=limit,
            offset=offset
        )

        logger.info(
            "Audit logs retrieved",
            filters={
                "item_id": item_id,
                "moderator_id": moderator_id,
                "action": action,
                "limit": limit,
                "offset": offset
            },
            count=len(logs)
        )

        return logs
    except Exception as e:
        logger.error("Failed to retrieve audit logs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
