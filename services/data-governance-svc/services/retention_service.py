"""
Retention Policy Service - Business logic for data retention policies
"""

import structlog
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text

from ..models import RetentionPolicy, EntityType, DataInventoryItem
from ..schemas.retention import (
    RetentionPolicyCreate, RetentionPolicyUpdate, RetentionPolicyResponse,
    RetentionPolicyValidation, RetentionPolicyImpact
)

logger = structlog.get_logger()


class RetentionPolicyService:
    """Service for managing retention policies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_policy(
        self,
        entity_type: EntityType,
        tenant_id: Optional[str],
        policy_data: RetentionPolicyCreate
    ) -> RetentionPolicyResponse:
        """Create a new retention policy."""
        logger.info(
            "Creating retention policy",
            entity_type=entity_type,
            tenant_id=tenant_id,
            retention_days=policy_data.retention_days
        )

        policy = RetentionPolicy(
            entity_type=entity_type,
            tenant_id=tenant_id,
            **policy_data.dict()
        )

        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)

        logger.info("Retention policy created", policy_id=policy.id)
        return RetentionPolicyResponse.model_validate(policy)

    async def get_policy(
        self,
        entity_type: EntityType,
        tenant_id: Optional[str] = None
    ) -> Optional[RetentionPolicyResponse]:
        """Get retention policy for entity type and tenant."""
        query = select(RetentionPolicy).where(
            RetentionPolicy.entity_type == entity_type
        )

        if tenant_id:
            query = query.where(RetentionPolicy.tenant_id == tenant_id)
        else:
            query = query.where(RetentionPolicy.tenant_id.is_(None))

        result = await self.db.execute(query)
        policy = result.scalar_one_or_none()

        if policy:
            return RetentionPolicyResponse.model_validate(policy)
        return None

    async def list_policies(
        self,
        entity_type: Optional[EntityType] = None,
        tenant_id: Optional[str] = None
    ) -> List[RetentionPolicyResponse]:
        """List retention policies with optional filtering."""
        query = select(RetentionPolicy)

        conditions = []
        if entity_type:
            conditions.append(RetentionPolicy.entity_type == entity_type)
        if tenant_id:
            conditions.append(RetentionPolicy.tenant_id == tenant_id)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(RetentionPolicy.created_at.desc())
        result = await self.db.execute(query)
        policies = result.scalars().all()

        return [RetentionPolicyResponse.model_validate(policy) for policy in policies]

    async def update_policy(
        self,
        policy_id: str,
        update_data: RetentionPolicyUpdate
    ) -> Optional[RetentionPolicyResponse]:
        """Update retention policy."""
        query = select(RetentionPolicy).where(RetentionPolicy.id == policy_id)
        result = await self.db.execute(query)
        policy = result.scalar_one_or_none()

        if not policy:
            return None

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(policy, field):
                setattr(policy, field, value)

        await self.db.commit()
        await self.db.refresh(policy)

        logger.info("Retention policy updated", policy_id=policy_id)
        return RetentionPolicyResponse.model_validate(policy)

    async def delete_policy(
        self,
        entity_type: EntityType,
        tenant_id: Optional[str] = None
    ) -> bool:
        """Delete retention policy."""
        query = select(RetentionPolicy).where(
            RetentionPolicy.entity_type == entity_type
        )

        if tenant_id:
            query = query.where(RetentionPolicy.tenant_id == tenant_id)
        else:
            query = query.where(RetentionPolicy.tenant_id.is_(None))

        result = await self.db.execute(query)
        policy = result.scalar_one_or_none()

        if not policy:
            return False

        await self.db.delete(policy)
        await self.db.commit()

        logger.info("Retention policy deleted", policy_id=policy.id)
        return True

    async def validate_policy(
        self,
        entity_type: EntityType,
        tenant_id: Optional[str],
        policy_data: RetentionPolicyCreate
    ) -> RetentionPolicyValidation:
        """Validate retention policy configuration."""
        warnings = []
        errors = []
        recommendations = []

        # Check retention period
        if policy_data.retention_days < 30:
            warnings.append("Retention period less than 30 days may not provide sufficient data for business operations")

        if policy_data.retention_days > 2555:  # 7 years
            warnings.append("Retention period exceeds 7 years, which may create unnecessary compliance burden")

        # FERPA specific validation
        if policy_data.compliance_framework == "FERPA" and entity_type == EntityType.STUDENT:
            if policy_data.retention_days < 1825:  # 5 years
                recommendations.append("FERPA recommends retaining educational records for at least 5 years")

        # COPPA specific validation
        if policy_data.compliance_framework == "COPPA" and entity_type == EntityType.USER:
            if policy_data.retention_days > 365:
                warnings.append("COPPA recommends minimal data retention for children under 13")

        # Grace period validation
        if policy_data.grace_period_days > 90:
            warnings.append("Grace period exceeds 90 days, which may delay compliance")

        # Check for conflicting policies
        existing_policy = await self.get_policy(entity_type, tenant_id)
        if existing_policy:
            warnings.append(f"Existing policy found for {entity_type.value} - this will update the existing policy")

        is_valid = len(errors) == 0

        return RetentionPolicyValidation(
            is_valid=is_valid,
            warnings=warnings,
            errors=errors,
            recommendations=recommendations
        )

    async def get_policy_impact(
        self,
        entity_type: EntityType,
        tenant_id: Optional[str] = None
    ) -> RetentionPolicyImpact:
        """Get impact analysis of retention policy."""
        policy = await self.get_policy(entity_type, tenant_id)

        if not policy:
            return RetentionPolicyImpact(
                entity_type=entity_type,
                tenant_id=tenant_id,
                current_data_count=0,
                data_to_delete=0,
                data_under_legal_hold=0,
                estimated_deletion_date=None,
                storage_savings_mb=0.0,
                affected_subjects=[]
            )

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)

        # Query data inventory for impact analysis
        base_query = select(DataInventoryItem).where(
            DataInventoryItem.entity_type == entity_type,
            DataInventoryItem.is_deleted == False
        )

        if tenant_id:
            base_query = base_query.where(DataInventoryItem.tenant_id == tenant_id)

        # Current data count
        current_count_result = await self.db.execute(
            select(func.count(DataInventoryItem.id)).select_from(base_query.subquery())
        )
        current_data_count = current_count_result.scalar() or 0

        # Data to delete (past retention period)
        delete_query = base_query.where(
            DataInventoryItem.created_at < cutoff_date,
            DataInventoryItem.has_legal_hold == False
        )
        delete_count_result = await self.db.execute(
            select(func.count(DataInventoryItem.id)).select_from(delete_query.subquery())
        )
        data_to_delete = delete_count_result.scalar() or 0

        # Data under legal hold
        hold_query = base_query.where(DataInventoryItem.has_legal_hold == True)
        hold_count_result = await self.db.execute(
            select(func.count(DataInventoryItem.id)).select_from(hold_query.subquery())
        )
        data_under_legal_hold = hold_count_result.scalar() or 0

        # Affected subjects
        subjects_query = select(DataInventoryItem.entity_id.distinct()).select_from(delete_query.subquery())
        subjects_result = await self.db.execute(subjects_query)
        affected_subjects = [row[0] for row in subjects_result.fetchall()]

        # Estimated deletion date
        estimated_deletion_date = None
        if policy.auto_delete_enabled and data_to_delete > 0:
            estimated_deletion_date = datetime.utcnow() + timedelta(days=policy.grace_period_days)

        return RetentionPolicyImpact(
            entity_type=entity_type,
            tenant_id=tenant_id,
            current_data_count=current_data_count,
            data_to_delete=data_to_delete,
            data_under_legal_hold=data_under_legal_hold,
            estimated_deletion_date=estimated_deletion_date,
            storage_savings_mb=float(data_to_delete * 0.1),  # Estimated 0.1MB per record
            affected_subjects=affected_subjects
        )

    async def bulk_update_policies(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk update multiple retention policies."""
        results = []

        for update_item in updates:
            try:
                entity_type = EntityType(update_item["entity_type"])
                tenant_id = update_item.get("tenant_id")
                policy_data = RetentionPolicyCreate(**update_item["policy_data"])

                # Check if policy exists
                existing_policy = await self.get_policy(entity_type, tenant_id)

                if existing_policy:
                    # Update
                    update_data = RetentionPolicyUpdate(**policy_data.dict(), updated_by=policy_data.created_by)
                    result = await self.update_policy(existing_policy.id, update_data)
                else:
                    # Create
                    result = await self.create_policy(entity_type, tenant_id, policy_data)

                results.append({
                    "entity_type": entity_type.value,
                    "tenant_id": tenant_id,
                    "success": True,
                    "policy_id": result.id if result else None
                })

            except Exception as e:
                logger.error("Failed to update policy in bulk", error=str(e), update_item=update_item)
                results.append({
                    "entity_type": update_item.get("entity_type"),
                    "tenant_id": update_item.get("tenant_id"),
                    "success": False,
                    "error": str(e)
                })

        return results
