"""
Legal Hold Service - Business logic for legal holds management
"""

import structlog
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_

from ..models import (
    LegalHold, LegalHoldStatus, EntityType, DSRRequest, DSRStatus,
    DataInventoryItem
)
from ..schemas.legal_holds import (
    LegalHoldCreate, LegalHoldUpdate, LegalHoldResponse,
    LegalHoldImpactResponse, LegalHoldConflict, LegalHoldSummary
)

logger = structlog.get_logger()


class LegalHoldService:
    """Service for managing legal holds."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_hold(self, hold_data: LegalHoldCreate) -> LegalHoldResponse:
        """Create a new legal hold."""
        logger.info(
            "Creating legal hold",
            name=hold_data.name,
            entity_types=hold_data.entity_types,
            case_number=hold_data.case_number
        )

        hold = LegalHold(
            **hold_data.dict()
        )

        self.db.add(hold)
        await self.db.commit()
        await self.db.refresh(hold)

        # Update data inventory to mark affected items
        await self._update_data_inventory_holds(hold)

        logger.info("Legal hold created", hold_id=hold.id)
        return LegalHoldResponse.model_validate(hold)

    async def get_hold(self, hold_id: str) -> Optional[LegalHoldResponse]:
        """Get legal hold by ID."""
        query = select(LegalHold).where(LegalHold.id == hold_id)
        result = await self.db.execute(query)
        hold = result.scalar_one_or_none()

        if hold:
            return LegalHoldResponse.model_validate(hold)
        return None

    async def list_holds(
        self,
        status: Optional[LegalHoldStatus] = None,
        tenant_id: Optional[str] = None,
        case_number: Optional[str] = None,
        entity_type: Optional[EntityType] = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[LegalHoldResponse], int]:
        """List legal holds with filtering and pagination."""
        query = select(LegalHold)
        count_query = select(func.count(LegalHold.id))

        conditions = []

        if status:
            conditions.append(LegalHold.status == status)

        if active_only:
            conditions.append(
                and_(
                    LegalHold.status == LegalHoldStatus.ACTIVE,
                    or_(
                        LegalHold.expiry_date.is_(None),
                        LegalHold.expiry_date > datetime.utcnow()
                    )
                )
            )

        if tenant_id:
            conditions.append(LegalHold.tenant_id == tenant_id)

        if case_number:
            conditions.append(LegalHold.case_number == case_number)

        if entity_type:
            # Check if entity_type is in the JSON array
            conditions.append(LegalHold.entity_types.contains([entity_type.value]))

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated results
        query = query.order_by(LegalHold.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        holds = result.scalars().all()

        return [LegalHoldResponse.model_validate(hold) for hold in holds], total

    async def update_hold(
        self,
        hold_id: str,
        hold_data: LegalHoldUpdate
    ) -> Optional[LegalHoldResponse]:
        """Update legal hold."""
        query = select(LegalHold).where(LegalHold.id == hold_id)
        result = await self.db.execute(query)
        hold = result.scalar_one_or_none()

        if not hold:
            return None

        # Update fields
        update_dict = hold_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(hold, field):
                setattr(hold, field, value)

        await self.db.commit()
        await self.db.refresh(hold)

        # Update data inventory if entity types or subjects changed
        if 'entity_types' in update_dict or 'subject_ids' in update_dict:
            await self._update_data_inventory_holds(hold)

        logger.info("Legal hold updated", hold_id=hold_id)
        return LegalHoldResponse.model_validate(hold)

    async def release_hold(
        self,
        hold_id: str,
        release_reason: Optional[str] = None
    ) -> bool:
        """Release (deactivate) a legal hold."""
        query = select(LegalHold).where(LegalHold.id == hold_id)
        result = await self.db.execute(query)
        hold = result.scalar_one_or_none()

        if not hold or hold.status != LegalHoldStatus.ACTIVE:
            return False

        hold.status = LegalHoldStatus.RELEASED
        hold.released_at = datetime.utcnow()

        await self.db.commit()

        # Update data inventory to remove hold flags
        await self._remove_data_inventory_holds(hold)

        # Check and unblock any DSR requests
        await self._unblock_dsr_requests(hold)

        logger.info("Legal hold released", hold_id=hold_id, reason=release_reason)
        return True

    async def get_hold_impact(self, hold_id: str) -> Optional[LegalHoldImpactResponse]:
        """Get impact analysis of legal hold."""
        hold = await self.get_hold(hold_id)
        if not hold:
            return None

        # Count affected entities by type
        affected_entities = {}
        for entity_type_str in hold.entity_types:
            entity_type = EntityType(entity_type_str)

            query = select(func.count(DataInventoryItem.id)).where(
                DataInventoryItem.entity_type == entity_type,
                DataInventoryItem.has_legal_hold == True,
                DataInventoryItem.is_deleted == False
            )

            if hold.tenant_id:
                query = query.where(DataInventoryItem.tenant_id == hold.tenant_id)

            if hold.subject_ids:
                query = query.where(DataInventoryItem.entity_id.in_(hold.subject_ids))

            result = await self.db.execute(query)
            count = result.scalar() or 0
            affected_entities[entity_type] = count

        # Get blocked DSR requests
        blocked_requests_query = select(DSRRequest.id).where(
            DSRRequest.status == DSRStatus.BLOCKED
        ).join(DSRRequest.blocked_by_holds).where(
            LegalHold.id == hold_id
        )

        blocked_result = await self.db.execute(blocked_requests_query)
        blocked_requests = [row[0] for row in blocked_result.fetchall()]

        # Calculate total data items and subjects
        total_data_items = sum(affected_entities.values())

        subjects_query = select(DataInventoryItem.entity_id.distinct()).where(
            DataInventoryItem.has_legal_hold == True,
            DataInventoryItem.is_deleted == False
        )

        if hold.subject_ids:
            subjects_query = subjects_query.where(DataInventoryItem.entity_id.in_(hold.subject_ids))

        subjects_result = await self.db.execute(subjects_query)
        subjects_under_hold = [row[0] for row in subjects_result.fetchall()]

        return LegalHoldImpactResponse(
            hold_id=hold.id,
            hold_name=hold.name,
            affected_entities=affected_entities,
            blocked_dsr_requests=blocked_requests,
            total_data_items_protected=total_data_items,
            estimated_storage_mb=float(total_data_items * 0.1),  # Estimated 0.1MB per item
            subjects_under_hold=subjects_under_hold
        )

    async def extend_hold(
        self,
        hold_id: str,
        new_expiry_date: Optional[datetime] = None,
        extension_reason: Optional[str] = None
    ) -> bool:
        """Extend the expiry date of a legal hold."""
        query = select(LegalHold).where(LegalHold.id == hold_id)
        result = await self.db.execute(query)
        hold = result.scalar_one_or_none()

        if not hold or hold.status != LegalHoldStatus.ACTIVE:
            return False

        hold.expiry_date = new_expiry_date
        await self.db.commit()

        logger.info(
            "Legal hold extended",
            hold_id=hold_id,
            new_expiry=new_expiry_date.isoformat() if new_expiry_date else "indefinite",
            reason=extension_reason
        )
        return True

    async def get_blocked_requests(self, hold_id: str) -> List[Dict[str, Any]]:
        """Get DSR requests blocked by this legal hold."""
        query = select(DSRRequest).join(DSRRequest.blocked_by_holds).where(
            LegalHold.id == hold_id
        )

        result = await self.db.execute(query)
        requests = result.scalars().all()

        return [
            {
                "id": req.id,
                "dsr_type": req.dsr_type.value,
                "subject_id": req.subject_id,
                "subject_type": req.subject_type.value,
                "requested_at": req.requested_at.isoformat(),
                "requester_email": req.requester_email
            }
            for req in requests
        ]

    async def check_deletion_conflicts(
        self,
        subject_ids: List[str],
        entity_types: List[EntityType],
        tenant_id: Optional[str] = None
    ) -> List[LegalHoldConflict]:
        """Check if subjects have active legal holds that would block deletion."""
        conflicts = []

        # Get active legal holds
        query = select(LegalHold).where(
            LegalHold.status == LegalHoldStatus.ACTIVE,
            or_(
                LegalHold.expiry_date.is_(None),
                LegalHold.expiry_date > datetime.utcnow()
            )
        )

        if tenant_id:
            query = query.where(
                or_(
                    LegalHold.tenant_id == tenant_id,
                    LegalHold.tenant_id.is_(None)
                )
            )

        result = await self.db.execute(query)
        active_holds = result.scalars().all()

        # Check each subject against active holds
        for subject_id in subject_ids:
            for entity_type in entity_types:
                conflicting_holds = []

                for hold in active_holds:
                    # Check if hold applies to this entity type
                    if entity_type.value in hold.entity_types:
                        # Check if hold applies to this specific subject
                        if not hold.subject_ids or subject_id in hold.subject_ids:
                            conflicting_holds.append({
                                "id": hold.id,
                                "name": hold.name,
                                "case_number": hold.case_number,
                                "effective_date": hold.effective_date.isoformat(),
                                "expiry_date": hold.expiry_date.isoformat() if hold.expiry_date else None
                            })

                if conflicting_holds:
                    conflicts.append(LegalHoldConflict(
                        subject_id=subject_id,
                        entity_type=entity_type,
                        conflicting_holds=conflicting_holds,
                        conflict_reason=f"Subject {subject_id} of type {entity_type.value} is under {len(conflicting_holds)} active legal hold(s)"
                    ))

        return conflicts

    async def get_active_holds_summary(
        self,
        tenant_id: Optional[str] = None
    ) -> LegalHoldSummary:
        """Get summary of all active legal holds."""
        query = select(LegalHold).where(
            LegalHold.status == LegalHoldStatus.ACTIVE,
            or_(
                LegalHold.expiry_date.is_(None),
                LegalHold.expiry_date > datetime.utcnow()
            )
        )

        if tenant_id:
            query = query.where(LegalHold.tenant_id == tenant_id)

        result = await self.db.execute(query)
        active_holds = result.scalars().all()

        # Calculate statistics
        total_active_holds = len(active_holds)
        holds_by_entity_type = {}
        holds_expiring_soon = []
        oldest_hold = None

        thirty_days_from_now = datetime.utcnow() + timedelta(days=30)

        for hold in active_holds:
            # Count by entity type
            for entity_type in hold.entity_types:
                holds_by_entity_type[EntityType(entity_type)] = holds_by_entity_type.get(EntityType(entity_type), 0) + 1

            # Check expiring soon
            if hold.expiry_date and hold.expiry_date <= thirty_days_from_now:
                holds_expiring_soon.append({
                    "id": hold.id,
                    "name": hold.name,
                    "expiry_date": hold.expiry_date.isoformat(),
                    "days_until_expiry": (hold.expiry_date - datetime.utcnow()).days
                })

            # Find oldest
            if not oldest_hold or hold.effective_date < oldest_hold["effective_date"]:
                oldest_hold = {
                    "id": hold.id,
                    "name": hold.name,
                    "effective_date": hold.effective_date.isoformat(),
                    "days_active": (datetime.utcnow() - hold.effective_date).days
                }

        # Count protected subjects
        subjects_query = select(func.count(DataInventoryItem.entity_id.distinct())).where(
            DataInventoryItem.has_legal_hold == True,
            DataInventoryItem.is_deleted == False
        )

        if tenant_id:
            subjects_query = subjects_query.where(DataInventoryItem.tenant_id == tenant_id)

        subjects_result = await self.db.execute(subjects_query)
        total_subjects_protected = subjects_result.scalar() or 0

        # Count blocked deletions
        blocked_query = select(func.count(DSRRequest.id)).where(
            DSRRequest.status == DSRStatus.BLOCKED
        )

        if tenant_id:
            blocked_query = blocked_query.where(DSRRequest.tenant_id == tenant_id)

        blocked_result = await self.db.execute(blocked_query)
        total_blocked_deletions = blocked_result.scalar() or 0

        return LegalHoldSummary(
            total_active_holds=total_active_holds,
            holds_by_entity_type=holds_by_entity_type,
            holds_expiring_soon=holds_expiring_soon,
            oldest_active_hold=oldest_hold,
            total_subjects_protected=total_subjects_protected,
            total_blocked_deletions=total_blocked_deletions
        )

    async def bulk_release_holds(
        self,
        hold_ids: List[str],
        release_reason: str
    ) -> List[Dict[str, Any]]:
        """Release multiple legal holds at once."""
        results = []

        for hold_id in hold_ids:
            try:
                success = await self.release_hold(hold_id, release_reason)
                results.append({
                    "hold_id": hold_id,
                    "success": success,
                    "error": None
                })
            except Exception as e:
                logger.error("Failed to release hold in bulk", hold_id=hold_id, error=str(e))
                results.append({
                    "hold_id": hold_id,
                    "success": False,
                    "error": str(e)
                })

        logger.info("Bulk hold release completed", total=len(hold_ids), successful=len([r for r in results if r["success"]]))
        return results

    async def _update_data_inventory_holds(self, hold: LegalHold) -> None:
        """Update data inventory to mark items under legal hold."""
        for entity_type_str in hold.entity_types:
            entity_type = EntityType(entity_type_str)

            query = select(DataInventoryItem).where(
                DataInventoryItem.entity_type == entity_type,
                DataInventoryItem.is_deleted == False
            )

            if hold.tenant_id:
                query = query.where(DataInventoryItem.tenant_id == hold.tenant_id)

            if hold.subject_ids:
                query = query.where(DataInventoryItem.entity_id.in_(hold.subject_ids))

            result = await self.db.execute(query)
            items = result.scalars().all()

            for item in items:
                item.has_legal_hold = True

            await self.db.commit()

    async def _remove_data_inventory_holds(self, hold: LegalHold) -> None:
        """Remove legal hold flags from data inventory items."""
        for entity_type_str in hold.entity_types:
            entity_type = EntityType(entity_type_str)

            query = select(DataInventoryItem).where(
                DataInventoryItem.entity_type == entity_type,
                DataInventoryItem.has_legal_hold == True
            )

            if hold.tenant_id:
                query = query.where(DataInventoryItem.tenant_id == hold.tenant_id)

            if hold.subject_ids:
                query = query.where(DataInventoryItem.entity_id.in_(hold.subject_ids))

            result = await self.db.execute(query)
            items = result.scalars().all()

            # Check if items are still under other holds
            for item in items:
                other_holds = await self._check_other_active_holds(item, hold.id)
                if not other_holds:
                    item.has_legal_hold = False

            await self.db.commit()

    async def _check_other_active_holds(
        self,
        item: DataInventoryItem,
        excluding_hold_id: str
    ) -> bool:
        """Check if data item is still under other active legal holds."""
        query = select(LegalHold).where(
            LegalHold.id != excluding_hold_id,
            LegalHold.status == LegalHoldStatus.ACTIVE,
            or_(
                LegalHold.expiry_date.is_(None),
                LegalHold.expiry_date > datetime.utcnow()
            )
        )

        result = await self.db.execute(query)
        other_holds = result.scalars().all()

        for hold in other_holds:
            if item.entity_type.value in hold.entity_types:
                if not hold.subject_ids or item.entity_id in hold.subject_ids:
                    if not hold.tenant_id or hold.tenant_id == item.tenant_id:
                        return True

        return False

    async def _unblock_dsr_requests(self, hold: LegalHold) -> None:
        """Unblock DSR requests that were blocked by this hold."""
        # Get requests blocked by this hold
        query = select(DSRRequest).join(DSRRequest.blocked_by_holds).where(
            LegalHold.id == hold.id,
            DSRRequest.status == DSRStatus.BLOCKED
        )

        result = await self.db.execute(query)
        blocked_requests = result.scalars().all()

        for request in blocked_requests:
            # Remove this hold from the request's blocked holds
            request.blocked_by_holds = [h for h in request.blocked_by_holds if h.id != hold.id]

            # If no more blocking holds, change status to pending
            if not request.blocked_by_holds:
                request.status = DSRStatus.PENDING

        await self.db.commit()

        logger.info("Unblocked DSR requests", hold_id=hold.id, count=len(blocked_requests))
