"""Business logic services for Device Policy Service."""

import hashlib
import json
from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AllowlistEntry,
    DevicePolicy,
    Policy,
    PolicyStatus,
    PolicySyncLog,
    SyncStatus,
)
from app.schemas import (
    AllowlistEntryCreate,
    AllowlistEntryUpdate,
    PolicyCreate,
    PolicyDiff,
    PolicySyncRequest,
    PolicySyncResponse,
    PolicyUpdate,
)

logger = structlog.get_logger(__name__)


class PolicyService:
    """Service for managing device policies."""

    @staticmethod
    def calculate_checksum(config: dict) -> str:
        """Calculate checksum for policy configuration."""
        config_str = json.dumps(config, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(config_str.encode()).hexdigest()

    async def create_policy(
        self,
        policy_data: PolicyCreate,
        db: AsyncSession,
        created_by: str | None = None,
    ) -> Policy:
        """Create a new policy."""
        logger.info("Creating new policy", name=policy_data.name)

        # Calculate checksum
        checksum = self.calculate_checksum(policy_data.config)

        # Create policy
        policy = Policy(
            name=policy_data.name,
            description=policy_data.description,
            policy_type=policy_data.policy_type,
            config=policy_data.config,
            target_criteria=policy_data.target_criteria,
            priority=policy_data.priority,
            effective_from=policy_data.effective_from,
            effective_until=policy_data.effective_until,
            checksum=checksum,
            created_by=created_by,
            tenant_id=policy_data.tenant_id,
        )

        db.add(policy)
        await db.commit()
        await db.refresh(policy)

        logger.info("Policy created successfully", policy_id=policy.policy_id)
        return policy

    async def get_policy(self, policy_id: UUID, db: AsyncSession) -> Policy | None:
        """Get policy by ID."""
        result = await db.execute(select(Policy).where(Policy.policy_id == policy_id))
        return result.scalar_one_or_none()

    async def update_policy(
        self,
        policy_id: UUID,
        policy_data: PolicyUpdate,
        db: AsyncSession,
    ) -> Policy | None:
        """Update an existing policy."""
        policy = await self.get_policy(policy_id, db)
        if not policy:
            return None

        logger.info("Updating policy", policy_id=policy_id)

        # Update fields
        if policy_data.name is not None:
            policy.name = policy_data.name
        if policy_data.description is not None:
            policy.description = policy_data.description
        if policy_data.config is not None:
            policy.config = policy_data.config
            policy.checksum = self.calculate_checksum(policy_data.config)
            policy.version += 1
        if policy_data.target_criteria is not None:
            policy.target_criteria = policy_data.target_criteria
        if policy_data.priority is not None:
            policy.priority = policy_data.priority
        if policy_data.effective_from is not None:
            policy.effective_from = policy_data.effective_from
        if policy_data.effective_until is not None:
            policy.effective_until = policy_data.effective_until
        if policy_data.status is not None:
            policy.status = policy_data.status

        await db.commit()
        await db.refresh(policy)

        logger.info("Policy updated successfully", policy_id=policy_id)
        return policy

    async def delete_policy(self, policy_id: UUID, db: AsyncSession) -> bool:
        """Delete a policy."""
        policy = await self.get_policy(policy_id, db)
        if not policy:
            return False

        logger.info("Deleting policy", policy_id=policy_id)

        await db.delete(policy)
        await db.commit()

        logger.info("Policy deleted successfully", policy_id=policy_id)
        return True

    async def list_policies(
        self,
        db: AsyncSession,
        policy_type: str | None = None,
        status: PolicyStatus | None = None,
        tenant_id: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[Policy], int]:
        """List policies with pagination and filters."""
        query = select(Policy)

        # Apply filters
        if policy_type:
            query = query.where(Policy.policy_type == policy_type)
        if status:
            query = query.where(Policy.status == status)
        if tenant_id:
            query = query.where(Policy.tenant_id == tenant_id)

        # Get total count
        count_result = await db.execute(text("SELECT COUNT(*) FROM policies"))
        total = count_result.scalar()

        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Policy.created_at.desc())

        result = await db.execute(query)
        policies = result.scalars().all()

        return list(policies), total

    async def assign_policy_to_device(
        self,
        device_id: UUID,
        policy_id: UUID,
        db: AsyncSession,
        assigned_by: str | None = None,
    ) -> DevicePolicy:
        """Assign a policy to a device."""
        logger.info("Assigning policy to device", device_id=device_id, policy_id=policy_id)

        # Check if assignment already exists
        existing = await db.execute(
            select(DevicePolicy).where(
                DevicePolicy.device_id == device_id,
                DevicePolicy.policy_id == policy_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Policy already assigned to device")

        # Create assignment
        assignment = DevicePolicy(
            device_id=device_id,
            policy_id=policy_id,
            assigned_by=assigned_by,
        )

        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        logger.info("Policy assigned successfully", assignment_id=assignment.assignment_id)
        return assignment

    async def get_device_policies(self, device_id: UUID, db: AsyncSession) -> list[DevicePolicy]:
        """Get all policies assigned to a device."""
        result = await db.execute(
            select(DevicePolicy)
            .options(selectinload(DevicePolicy.policy))
            .where(DevicePolicy.device_id == device_id)
        )
        return list(result.scalars().all())


class PolicySyncService:
    """Service for policy synchronization with devices."""

    def __init__(self, policy_service: PolicyService):
        self.policy_service = policy_service

    async def sync_policies(
        self, sync_request: PolicySyncRequest, db: AsyncSession
    ) -> PolicySyncResponse:
        """Synchronize policies with a device."""
        device_id = sync_request.device_id
        current_policies = sync_request.current_policies

        logger.info("Starting policy sync", device_id=device_id)

        # Get assigned policies for device
        device_policies = await self.policy_service.get_device_policies(device_id, db)

        # Determine sync type and generate diffs
        policies_diff = []
        sync_type = "full"

        for device_policy in device_policies:
            policy = device_policy.policy
            policy_id_str = str(policy.policy_id)
            current_version = current_policies.get(policy_id_str, 0)

            if policy.status != PolicyStatus.ACTIVE:
                continue

            if current_version == 0:
                # New policy
                policies_diff.append(
                    PolicyDiff(
                        policy_id=policy.policy_id,
                        action="add",
                        to_version=policy.version,
                        config=policy.config,
                        checksum=policy.checksum,
                    )
                )
            elif current_version < policy.version:
                # Updated policy
                policies_diff.append(
                    PolicyDiff(
                        policy_id=policy.policy_id,
                        action="update",
                        from_version=current_version,
                        to_version=policy.version,
                        config=policy.config,
                        checksum=policy.checksum,
                    )
                )
                sync_type = "diff"

        # Check for removed policies
        assigned_policy_ids = {str(dp.policy_id) for dp in device_policies}
        for policy_id_str in current_policies:
            if policy_id_str not in assigned_policy_ids:
                policies_diff.append(
                    PolicyDiff(
                        policy_id=UUID(policy_id_str),
                        action="remove",
                        from_version=current_policies[policy_id_str],
                    )
                )
                sync_type = "diff"

        # Update device policy sync status
        for device_policy in device_policies:
            device_policy.sync_status = SyncStatus.SYNCED
            device_policy.last_sync_at = datetime.utcnow()
            device_policy.applied_version = device_policy.policy.version
            device_policy.applied_checksum = device_policy.policy.checksum

        await db.commit()

        # Log sync activity
        for diff in policies_diff:
            sync_log = PolicySyncLog(
                device_id=device_id,
                policy_id=diff.policy_id,
                sync_type=sync_type,
                sync_status=SyncStatus.SYNCED,
                from_version=diff.from_version,
                to_version=diff.to_version,
            )
            db.add(sync_log)

        await db.commit()

        logger.info(
            "Policy sync completed",
            device_id=device_id,
            sync_type=sync_type,
            policy_count=len(policies_diff),
        )

        return PolicySyncResponse(
            device_id=device_id,
            sync_type=sync_type,
            policies=policies_diff,
        )

    async def long_poll_sync(
        self,
        device_id: UUID,
        current_policies: dict[str, int],
        db: AsyncSession,
        timeout: int = 300,
    ) -> PolicySyncResponse | None:
        """Long polling for policy updates."""
        # For now, return immediate sync result
        # In production, implement actual long polling with WebSockets or SSE
        sync_request = PolicySyncRequest(device_id=device_id, current_policies=current_policies)
        return await self.sync_policies(sync_request, db)


class AllowlistService:
    """Service for managing network allowlist entries."""

    async def create_entry(
        self,
        entry_data: AllowlistEntryCreate,
        db: AsyncSession,
        created_by: str | None = None,
    ) -> AllowlistEntry:
        """Create a new allowlist entry."""
        logger.info("Creating allowlist entry", value=entry_data.value)

        entry = AllowlistEntry(
            entry_type=entry_data.entry_type,
            value=entry_data.value,
            description=entry_data.description,
            category=entry_data.category,
            tags=entry_data.tags,
            priority=entry_data.priority,
            created_by=created_by,
            tenant_id=entry_data.tenant_id,
        )

        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        logger.info("Allowlist entry created", entry_id=entry.entry_id)
        return entry

    async def get_entry(self, entry_id: UUID, db: AsyncSession) -> AllowlistEntry | None:
        """Get allowlist entry by ID."""
        result = await db.execute(select(AllowlistEntry).where(AllowlistEntry.entry_id == entry_id))
        return result.scalar_one_or_none()

    async def update_entry(
        self,
        entry_id: UUID,
        entry_data: AllowlistEntryUpdate,
        db: AsyncSession,
    ) -> AllowlistEntry | None:
        """Update an allowlist entry."""
        entry = await self.get_entry(entry_id, db)
        if not entry:
            return None

        logger.info("Updating allowlist entry", entry_id=entry_id)

        # Update fields
        if entry_data.value is not None:
            entry.value = entry_data.value
        if entry_data.description is not None:
            entry.description = entry_data.description
        if entry_data.category is not None:
            entry.category = entry_data.category
        if entry_data.tags is not None:
            entry.tags = entry_data.tags
        if entry_data.priority is not None:
            entry.priority = entry_data.priority
        if entry_data.is_active is not None:
            entry.is_active = entry_data.is_active

        await db.commit()
        await db.refresh(entry)

        logger.info("Allowlist entry updated", entry_id=entry_id)
        return entry

    async def delete_entry(self, entry_id: UUID, db: AsyncSession) -> bool:
        """Delete an allowlist entry."""
        entry = await self.get_entry(entry_id, db)
        if not entry:
            return False

        logger.info("Deleting allowlist entry", entry_id=entry_id)

        await db.delete(entry)
        await db.commit()

        logger.info("Allowlist entry deleted", entry_id=entry_id)
        return True

    async def list_entries(
        self,
        db: AsyncSession,
        entry_type: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
        tenant_id: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[AllowlistEntry], int]:
        """List allowlist entries with pagination and filters."""
        query = select(AllowlistEntry)

        # Apply filters
        if entry_type:
            query = query.where(AllowlistEntry.entry_type == entry_type)
        if category:
            query = query.where(AllowlistEntry.category == category)
        if is_active is not None:
            query = query.where(AllowlistEntry.is_active == is_active)
        if tenant_id:
            query = query.where(AllowlistEntry.tenant_id == tenant_id)

        # Get total count
        count_result = await db.execute(text("SELECT COUNT(*) FROM allowlist_entries"))
        total = count_result.scalar()

        # Apply pagination
        offset = (page - 1) * size
        query = (
            query.offset(offset)
            .limit(size)
            .order_by(AllowlistEntry.priority.desc(), AllowlistEntry.created_at.desc())
        )

        result = await db.execute(query)
        entries = result.scalars().all()

        return list(entries), total

    async def get_active_allowlist(
        self, tenant_id: str | None = None, db: AsyncSession = None
    ) -> list[AllowlistEntry]:
        """Get all active allowlist entries for walled garden."""
        query = select(AllowlistEntry).where(AllowlistEntry.is_active.is_(True))

        if tenant_id:
            query = query.where(AllowlistEntry.tenant_id == tenant_id)

        query = query.order_by(AllowlistEntry.priority.desc())

        result = await db.execute(query)
        return list(result.scalars().all())
