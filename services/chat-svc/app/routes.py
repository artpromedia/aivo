"""
API routes for chat service.
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload

from .database import get_db
from .models import (
    ChatSession, ChatMessage, ParentalControl, ModerationLog, AuditEntry,
    UserRole, ChatType, MessageStatus, ModerationAction
)
from .schemas import (
    ChatSessionCreate, ChatSessionResponse, MessageCreate, MessageResponse,
    ParentalControlCreate, ParentalControlResponse, ParentalControlUpdate,
    ChatExportRequest, ChatDeleteRequest, ErrorResponse, ModerationStats,
    ChatSessionStats, AuditEntryResponse
)
from .moderation import ModerationService, PerspectiveConfig, create_content_hash
from .audit import AuditService, S3ExportService, MongoArchiveService

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()
security = HTTPBearer()

# Initialize services (these would be dependency injected in production)
def get_moderation_service() -> ModerationService:
    """Get moderation service instance."""
    perspective_config = PerspectiveConfig(
        api_key=os.getenv("PERSPECTIVE_API_KEY", ""),
        timeout=int(os.getenv("PERSPECTIVE_TIMEOUT", "10")),
        retry_attempts=int(os.getenv("PERSPECTIVE_RETRY_ATTEMPTS", "3"))
    )
    return ModerationService(perspective_config)

def get_audit_service() -> AuditService:
    """Get audit service instance."""
    s3_service = S3ExportService(
        bucket_name=os.getenv("S3_BUCKET_NAME", "aivo-chat-exports"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        region=os.getenv("AWS_REGION", "us-east-1")
    )
    
    mongo_service = None
    if os.getenv("MONGODB_CONNECTION_STRING"):
        mongo_service = MongoArchiveService(
            connection_string=os.getenv("MONGODB_CONNECTION_STRING"),
            database_name=os.getenv("MONGODB_DATABASE", "aivo_archive")
        )
    
    return AuditService(s3_service, mongo_service)

# Dependency to get current user (mock implementation)
async def get_current_user(token: str = Depends(security)) -> Dict[str, Any]:
    """Get current user from token."""
    # In production, this would validate JWT token and return user info
    return {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "role": "parent",
        "permissions": ["read", "write"]
    }


# Chat Session Endpoints
@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new chat session."""
    try:
        # Validate user permissions
        if session_data.parent_id and str(session_data.parent_id) != current_user["user_id"]:
            if current_user["role"] not in ["admin", "teacher"]:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Create session
        session = ChatSession(
            chat_type=session_data.chat_type,
            participants=session_data.participants,
            learner_id=session_data.learner_id,
            parent_id=session_data.parent_id,
            teacher_id=session_data.teacher_id,
            parental_controls_enabled=session_data.parental_controls_enabled,
            ai_tutor_enabled=session_data.ai_tutor_enabled,
            moderation_level=session_data.moderation_level
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Created chat session {session.id}")
        return session
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat session")


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    user_id: Optional[UUID] = Query(None),
    chat_type: Optional[ChatType] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get chat sessions."""
    try:
        query = select(ChatSession)
        
        # Apply filters
        if user_id:
            query = query.where(
                or_(
                    ChatSession.learner_id == user_id,
                    ChatSession.parent_id == user_id,
                    ChatSession.teacher_id == user_id
                )
            )
        
        if chat_type:
            query = query.where(ChatSession.chat_type == chat_type)
        
        if is_active is not None:
            query = query.where(ChatSession.is_active == is_active)
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        query = query.order_by(ChatSession.created_at.desc())
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat sessions")


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific chat session."""
    try:
        query = select(ChatSession).where(ChatSession.id == session_id)
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Check permissions
        user_id = UUID(current_user["user_id"])
        if user_id not in session.participants and current_user["role"] not in ["admin"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat session")


# Message Endpoints
@router.post("/messages", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    moderation_service: ModerationService = Depends(get_moderation_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Create a new message with moderation and audit trail."""
    try:
        # Verify session exists and user has permission
        session_query = select(ChatSession).where(ChatSession.id == message_data.session_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Check permissions
        if message_data.sender_id not in session.participants:
            raise HTTPException(status_code=403, detail="Sender not in session")
        
        # Create content hash
        content_hash = create_content_hash(message_data.content)
        
        # Create message
        message = ChatMessage(
            session_id=message_data.session_id,
            sender_id=message_data.sender_id,
            sender_role=message_data.sender_role,
            original_content=message_data.content,
            content_hash=content_hash,
            message_type=message_data.message_type,
            status=MessageStatus.PENDING
        )
        
        db.add(message)
        await db.flush()  # Get message ID without committing
        
        # Moderate message
        moderation_result = await moderation_service.moderate_message(
            message_data.content,
            session.moderation_level
        )
        
        # Update message based on moderation
        if moderation_result.action == ModerationAction.APPROVED:
            message.status = MessageStatus.APPROVED
        elif moderation_result.action in [ModerationAction.SOFT_BLOCK, ModerationAction.HARD_BLOCK]:
            message.status = MessageStatus.BLOCKED
        elif moderation_result.action == ModerationAction.PII_SCRUBBED:
            pii_result = moderation_service.pii_detector.detect_pii(message_data.content)
            message.processed_content = pii_result.scrubbed_content
            message.contains_pii = True
            message.pii_types = pii_result.pii_types
            message.status = MessageStatus.APPROVED
        else:
            message.status = MessageStatus.FLAGGED
        
        message.moderation_score = moderation_result.confidence
        message.moderation_action = moderation_result.action
        
        # Create moderation log
        mod_log = ModerationLog(
            message_id=message.id,
            moderation_service="perspective_api",
            moderation_version="1.0",
            toxicity_score=moderation_result.toxicity_score,
            threat_score=moderation_result.threat_score,
            profanity_score=moderation_result.profanity_score,
            identity_attack_score=moderation_result.identity_attack_score,
            action_taken=moderation_result.action,
            reason=moderation_result.reason,
            confidence=moderation_result.confidence,
            processing_time_ms=moderation_result.processing_time_ms
        )
        
        db.add(mod_log)
        
        # Get previous audit entry for chain
        prev_audit_query = select(AuditEntry).order_by(AuditEntry.timestamp.desc()).limit(1)
        prev_audit_result = await db.execute(prev_audit_query)
        previous_audit = prev_audit_result.scalar_one_or_none()
        
        # Create audit entry
        background_tasks.add_task(
            audit_service.create_audit_entry,
            db, message, previous_audit
        )
        
        await db.commit()
        await db.refresh(message)
        
        logger.info(f"Created message {message.id} with status {message.status}")
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create message: {e}")
        raise HTTPException(status_code=500, detail="Failed to create message")


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: UUID,
    include_blocked: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get messages for a chat session."""
    try:
        # Check session access
        session_query = select(ChatSession).where(ChatSession.id == session_id)
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        user_id = UUID(current_user["user_id"])
        if user_id not in session.participants and current_user["role"] not in ["admin"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build query
        query = select(ChatMessage).where(ChatMessage.session_id == session_id)
        
        if not include_blocked:
            query = query.where(ChatMessage.status != MessageStatus.BLOCKED)
        
        query = query.order_by(ChatMessage.created_at.asc())
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session messages")


# Parental Control Endpoints
@router.post("/parental-controls", response_model=ParentalControlResponse)
async def create_parental_control(
    control_data: ParentalControlCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create parental control settings."""
    try:
        # Verify parent permission
        if str(control_data.parent_id) != current_user["user_id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Check if controls already exist
        existing_query = select(ParentalControl).where(
            and_(
                ParentalControl.parent_id == control_data.parent_id,
                ParentalControl.learner_id == control_data.learner_id
            )
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Parental controls already exist")
        
        # Create controls
        controls = ParentalControl(**control_data.model_dump())
        db.add(controls)
        await db.commit()
        await db.refresh(controls)
        
        logger.info(f"Created parental controls {controls.id}")
        return controls
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create parental controls: {e}")
        raise HTTPException(status_code=500, detail="Failed to create parental controls")


@router.get("/parental-controls/{parent_id}/{learner_id}", response_model=ParentalControlResponse)
async def get_parental_control(
    parent_id: UUID,
    learner_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get parental control settings."""
    try:
        # Check permissions
        if str(parent_id) != current_user["user_id"] and current_user["role"] not in ["admin", "teacher"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        query = select(ParentalControl).where(
            and_(
                ParentalControl.parent_id == parent_id,
                ParentalControl.learner_id == learner_id
            )
        )
        result = await db.execute(query)
        controls = result.scalar_one_or_none()
        
        if not controls:
            raise HTTPException(status_code=404, detail="Parental controls not found")
        
        return controls
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get parental controls: {e}")
        raise HTTPException(status_code=500, detail="Failed to get parental controls")


@router.put("/parental-controls/{control_id}", response_model=ParentalControlResponse)
async def update_parental_control(
    control_id: UUID,
    update_data: ParentalControlUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update parental control settings."""
    try:
        # Get existing controls
        query = select(ParentalControl).where(ParentalControl.id == control_id)
        result = await db.execute(query)
        controls = result.scalar_one_or_none()
        
        if not controls:
            raise HTTPException(status_code=404, detail="Parental controls not found")
        
        # Check permissions
        if str(controls.parent_id) != current_user["user_id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Update fields
        update_data_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_data_dict.items():
            setattr(controls, field, value)
        
        controls.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(controls)
        
        logger.info(f"Updated parental controls {control_id}")
        return controls
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update parental controls: {e}")
        raise HTTPException(status_code=500, detail="Failed to update parental controls")


# Export and Delete Endpoints
@router.post("/export")
async def export_chat_data(
    export_request: ChatExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Export chat data to S3."""
    try:
        # Verify permissions
        if current_user["role"] not in ["admin", "parent", "teacher"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Build query for messages to export
        query = select(ChatMessage).options(selectinload(ChatMessage.session))
        
        if export_request.session_ids:
            query = query.where(ChatMessage.session_id.in_(export_request.session_ids))
        
        if export_request.start_date:
            query = query.where(ChatMessage.created_at >= export_request.start_date)
        
        if export_request.end_date:
            query = query.where(ChatMessage.created_at <= export_request.end_date)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        if not messages:
            raise HTTPException(status_code=404, detail="No messages found for export")
        
        # Group messages by session for export
        sessions_to_export = {}
        for message in messages:
            session_id = message.session_id
            if session_id not in sessions_to_export:
                sessions_to_export[session_id] = []
            sessions_to_export[session_id].append(message)
        
        # Schedule background export tasks
        export_keys = []
        for session_id, session_messages in sessions_to_export.items():
            s3_key = await audit_service.export_session_data(
                session_id,
                session_messages,
                export_request.export_format,
                export_request.include_pii
            )
            if s3_key:
                export_keys.append(s3_key)
        
        return {
            "message": f"Export initiated for {len(sessions_to_export)} sessions",
            "export_keys": export_keys,
            "total_messages": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export chat data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export chat data")


@router.delete("/messages")
async def delete_chat_data(
    delete_request: ChatDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete chat messages or sessions."""
    try:
        # Verify permissions
        if current_user["role"] not in ["admin", "parent"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        deleted_count = 0
        
        if delete_request.message_ids:
            # Delete specific messages
            if delete_request.hard_delete:
                # Hard delete - remove from database
                delete_query = (
                    update(ChatMessage)
                    .where(ChatMessage.id.in_(delete_request.message_ids))
                    .values(status=MessageStatus.ARCHIVED)
                )
            else:
                # Soft delete - mark as archived
                delete_query = (
                    update(ChatMessage)
                    .where(ChatMessage.id.in_(delete_request.message_ids))
                    .values(status=MessageStatus.ARCHIVED)
                )
            
            result = await db.execute(delete_query)
            deleted_count += result.rowcount
        
        if delete_request.session_ids:
            # Delete sessions and their messages
            for session_id in delete_request.session_ids:
                if delete_request.hard_delete:
                    # Mark session as inactive
                    session_update = (
                        update(ChatSession)
                        .where(ChatSession.id == session_id)
                        .values(is_active=False, ended_at=datetime.now(timezone.utc))
                    )
                    await db.execute(session_update)
                
                # Archive messages in session
                message_update = (
                    update(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .values(status=MessageStatus.ARCHIVED)
                )
                result = await db.execute(message_update)
                deleted_count += result.rowcount
        
        await db.commit()
        
        logger.info(f"Deleted {deleted_count} messages. Reason: {delete_request.reason}")
        return {
            "message": f"Successfully processed deletion request",
            "deleted_count": deleted_count,
            "hard_delete": delete_request.hard_delete
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete chat data: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat data")


# Statistics Endpoints
@router.get("/stats/moderation", response_model=ModerationStats)
async def get_moderation_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get moderation statistics."""
    try:
        if current_user["role"] not in ["admin", "teacher"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Build base query
        query = select(
            func.count(ChatMessage.id).label("total_messages"),
            func.sum(func.case((ChatMessage.status == MessageStatus.APPROVED, 1), else_=0)).label("approved"),
            func.sum(func.case((ChatMessage.status == MessageStatus.BLOCKED, 1), else_=0)).label("blocked"),
            func.sum(func.case((ChatMessage.status == MessageStatus.FLAGGED, 1), else_=0)).label("flagged"),
            func.avg(ModerationLog.processing_time_ms).label("avg_processing_time"),
            func.count(ModerationLog.id).label("moderation_calls"),
            func.sum(func.case((ChatMessage.contains_pii == True, 1), else_=0)).label("pii_detections")
        ).select_from(
            ChatMessage.__table__.join(ModerationLog.__table__, isouter=True)
        )
        
        if start_date:
            query = query.where(ChatMessage.created_at >= start_date)
        if end_date:
            query = query.where(ChatMessage.created_at <= end_date)
        
        result = await db.execute(query)
        row = result.first()
        
        return ModerationStats(
            total_messages=row.total_messages or 0,
            approved_messages=row.approved or 0,
            blocked_messages=row.blocked or 0,
            flagged_messages=row.flagged or 0,
            average_processing_time_ms=row.avg_processing_time or 0.0,
            perspective_api_calls=row.moderation_calls or 0,
            pii_detections=row.pii_detections or 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get moderation stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get moderation stats")


@router.get("/stats/sessions", response_model=ChatSessionStats)
async def get_session_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get chat session statistics."""
    try:
        if current_user["role"] not in ["admin", "teacher"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get basic session stats
        base_query = select(ChatSession)
        if start_date:
            base_query = base_query.where(ChatSession.created_at >= start_date)
        if end_date:
            base_query = base_query.where(ChatSession.created_at <= end_date)
        
        # Total and active sessions
        total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
        total_sessions = total_result.scalar()
        
        active_result = await db.execute(
            select(func.count()).select_from(
                base_query.where(ChatSession.is_active == True).subquery()
            )
        )
        active_sessions = active_result.scalar()
        
        # Sessions by type
        type_query = select(
            ChatSession.chat_type,
            func.count(ChatSession.id)
        ).group_by(ChatSession.chat_type)
        
        if start_date:
            type_query = type_query.where(ChatSession.created_at >= start_date)
        if end_date:
            type_query = type_query.where(ChatSession.created_at <= end_date)
        
        type_result = await db.execute(type_query)
        sessions_by_type = {row[0].value: row[1] for row in type_result}
        
        return ChatSessionStats(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            sessions_by_type=sessions_by_type,
            average_session_duration_minutes=0.0,  # Would need to calculate this
            messages_per_session=0.0  # Would need to calculate this
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session stats")


# Audit Endpoints
@router.get("/audit/{message_id}", response_model=List[AuditEntryResponse])
async def get_message_audit_trail(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get audit trail for a message."""
    try:
        if current_user["role"] not in ["admin", "teacher"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        query = select(AuditEntry).where(AuditEntry.message_id == message_id)
        result = await db.execute(query)
        audit_entries = result.scalars().all()
        
        return audit_entries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit trail")


# Dependency placeholder for database session
async def get_db_dependency():
    """Placeholder for database dependency."""
    pass
