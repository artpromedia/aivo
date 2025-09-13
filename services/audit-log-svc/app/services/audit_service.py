"""Audit logging service for creating immutable audit events."""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config import settings
from app.models.audit_event import AuditEvent

logger = structlog.get_logger(__name__)


class AuditService:
    """Service for managing immutable audit events with hash chain verification."""

    def __init__(self):
        self._lock = asyncio.Lock()

    async def create_audit_event(
        self,
        db: AsyncSession,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        before_state: Optional[dict[str, Any]] = None,
        after_state: Optional[dict[str, Any]] = None,
        actor_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        compliance_flags: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Create a new immutable audit event with hash chain verification.

        This method ensures thread-safety and maintains the hash chain integrity.
        """
        async with self._lock:
            try:
                # Get the previous hash for chain verification
                previous_hash = await self._get_latest_hash(db)

                # Calculate retention date based on settings
                retention_until = datetime.utcnow() + timedelta(days=settings.retention_days)

                # Create the audit event
                audit_event = AuditEvent.create_audit_event(
                    actor=actor,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    before_state=before_state,
                    after_state=after_state,
                    actor_role=actor_role,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    session_id=session_id,
                    metadata=metadata,
                    previous_hash=previous_hash,
                    retention_until=retention_until,
                    compliance_flags=compliance_flags,
                )

                # Save to database
                db.add(audit_event)
                await db.commit()
                await db.refresh(audit_event)

                logger.info(
                    "Audit event created",
                    audit_id=str(audit_event.id),
                    actor=actor,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    hash=audit_event.current_hash,
                    previous_hash=previous_hash,
                )

                return audit_event

            except Exception as e:
                await db.rollback()
                logger.error(
                    "Failed to create audit event",
                    error=str(e),
                    actor=actor,
                    action=action,
                    resource_type=resource_type,
                )
                raise

    async def _get_latest_hash(self, db: AsyncSession) -> Optional[str]:
        """Get the hash of the most recent audit event for chain verification."""
        stmt = (
            select(AuditEvent.current_hash)
            .order_by(desc(AuditEvent.timestamp), desc(AuditEvent.created_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def verify_hash_chain(
        self,
        db: AsyncSession,
        start_id: Optional[UUID] = None,
        end_id: Optional[UUID] = None,
    ) -> dict[str, Any]:
        """
        Verify the integrity of the hash chain.

        Args:
            db: Database session
            start_id: Start verification from this audit event ID
            end_id: End verification at this audit event ID

        Returns:
            Verification result with details
        """
        logger.info("Starting hash chain verification", start_id=start_id, end_id=end_id)

        # Build query for verification range
        conditions = []
        if start_id:
            conditions.append(AuditEvent.id >= start_id)
        if end_id:
            conditions.append(AuditEvent.id <= end_id)

        stmt = (
            select(AuditEvent)
            .where(and_(*conditions) if conditions else True)
            .order_by(AuditEvent.timestamp.asc(), AuditEvent.created_at.asc())
        )

        result = await db.execute(stmt)
        events = result.scalars().all()

        verification_result = {
            "is_valid": True,
            "total_events": len(events),
            "verified_events": 0,
            "invalid_events": [],
            "broken_chains": [],
            "verification_timestamp": datetime.utcnow().isoformat(),
        }

        previous_hash = None

        for i, event in enumerate(events):
            # Verify individual event hash
            if not event.verify_hash():
                verification_result["is_valid"] = False
                verification_result["invalid_events"].append({
                    "event_id": str(event.id),
                    "expected_hash": event.calculate_hash(event.previous_hash),
                    "actual_hash": event.current_hash,
                    "error": "Hash mismatch"
                })
                continue

            # Verify chain linkage
            if i > 0 and event.previous_hash != previous_hash:
                verification_result["is_valid"] = False
                verification_result["broken_chains"].append({
                    "event_id": str(event.id),
                    "expected_previous_hash": previous_hash,
                    "actual_previous_hash": event.previous_hash,
                    "error": "Chain broken"
                })

            verification_result["verified_events"] += 1
            previous_hash = event.current_hash

        logger.info(
            "Hash chain verification completed",
            is_valid=verification_result["is_valid"],
            total_events=verification_result["total_events"],
            verified_events=verification_result["verified_events"],
            invalid_count=len(verification_result["invalid_events"]),
            broken_chains=len(verification_result["broken_chains"]),
        )

        return verification_result

    async def get_audit_stats(self, db: AsyncSession) -> dict[str, Any]:
        """Get audit statistics for monitoring and reporting."""
        # Total events
        total_stmt = select(func.count(AuditEvent.id))
        total_result = await db.execute(total_stmt)
        total_events = total_result.scalar()

        # Events by action in last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_stmt = (
            select(AuditEvent.action, func.count(AuditEvent.id))
            .where(AuditEvent.timestamp >= last_24h)
            .group_by(AuditEvent.action)
        )
        recent_result = await db.execute(recent_stmt)
        recent_actions = dict(recent_result.all())

        # Events by actor in last 24 hours
        actor_stmt = (
            select(AuditEvent.actor, func.count(AuditEvent.id))
            .where(AuditEvent.timestamp >= last_24h)
            .group_by(AuditEvent.actor)
            .order_by(func.count(AuditEvent.id).desc())
            .limit(10)
        )
        actor_result = await db.execute(actor_stmt)
        top_actors = dict(actor_result.all())

        # Latest event timestamp
        latest_stmt = select(func.max(AuditEvent.timestamp))
        latest_result = await db.execute(latest_stmt)
        latest_timestamp = latest_result.scalar()

        return {
            "total_events": total_events,
            "recent_actions_24h": recent_actions,
            "top_actors_24h": top_actors,
            "latest_event_timestamp": latest_timestamp.isoformat() if latest_timestamp else None,
            "retention_days": settings.retention_days,
            "hash_chain_enabled": settings.enable_hash_chain,
        }

    async def search_audit_events(
        self,
        db: AsyncSession,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """
        Search audit events with filtering and pagination.

        Returns:
            Dictionary with events, pagination info, and metadata
        """
        # Validate page size
        page_size = min(page_size, settings.max_page_size)
        offset = (page - 1) * page_size

        # Build filter conditions
        conditions = []

        if actor:
            conditions.append(AuditEvent.actor.ilike(f"%{actor}%"))
        if action:
            conditions.append(AuditEvent.action == action)
        if resource_type:
            conditions.append(AuditEvent.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditEvent.resource_id == resource_id)
        if start_date:
            conditions.append(AuditEvent.timestamp >= start_date)
        if end_date:
            conditions.append(AuditEvent.timestamp <= end_date)
        if request_id:
            conditions.append(AuditEvent.request_id == request_id)
        if ip_address:
            conditions.append(AuditEvent.ip_address == ip_address)

        # Count total matching records
        count_stmt = select(func.count(AuditEvent.id)).where(and_(*conditions) if conditions else True)
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar()

        # Query events with pagination
        stmt = (
            select(AuditEvent)
            .where(and_(*conditions) if conditions else True)
            .order_by(desc(AuditEvent.timestamp))
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        events = result.scalars().all()

        return {
            "events": events,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
                "has_next": offset + page_size < total_count,
                "has_prev": page > 1,
            },
            "filters": {
                "actor": actor,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "request_id": request_id,
                "ip_address": ip_address,
            },
        }
