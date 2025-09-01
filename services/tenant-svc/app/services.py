"""
Service layer for tenant management and seat allocation.
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from .models import Tenant, Seat, UserTenantRole, SeatAudit, TenantKind, SeatState, UserRole
from .schemas import (
    TenantCreate, TenantUpdate, SeatCreate, SeatAllocate, SeatReclaim,
    SeatSummary, UserTenantRoleCreate, DistrictCreate, SchoolCreate
)


class TenantService:
    """Service for managing tenants (districts and schools)."""

    @staticmethod
    async def create_district(db: AsyncSession, district_data: DistrictCreate) -> Tenant:
        """Create a new district."""
        tenant_data = TenantCreate(
            name=district_data.name,
            kind=TenantKind.DISTRICT,
            parent_id=None
        )
        
        tenant = Tenant(**tenant_data.model_dump())
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def create_school(
        db: AsyncSession, 
        district_id: int, 
        school_data: SchoolCreate
    ) -> Tenant:
        """Create a new school under a district."""
        # Verify district exists and is actually a district
        district = await TenantService.get_tenant_by_id(db, district_id)
        if not district or district.kind != TenantKind.DISTRICT:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="District not found"
            )
        
        tenant_data = TenantCreate(
            name=school_data.name,
            kind=TenantKind.SCHOOL,
            parent_id=district_id
        )
        
        tenant = Tenant(**tenant_data.model_dump())
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def get_tenant_by_id(db: AsyncSession, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID."""
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_district_with_schools(db: AsyncSession, district_id: int) -> Optional[Tenant]:
        """Get district with all its schools."""
        result = await db.execute(
            select(Tenant)
            .options(selectinload(Tenant.children))
            .where(and_(Tenant.id == district_id, Tenant.kind == TenantKind.DISTRICT))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_tenant(
        db: AsyncSession, 
        tenant_id: int, 
        tenant_data: TenantUpdate
    ) -> Optional[Tenant]:
        """Update tenant information."""
        tenant = await TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return None
        
        update_data = tenant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        await db.commit()
        await db.refresh(tenant)
        return tenant


class SeatService:
    """Service for managing seat allocation and lifecycle."""

    @staticmethod
    async def purchase_seats(db: AsyncSession, seat_data: SeatCreate, user_id: str) -> List[Seat]:
        """Purchase (create) seats for a tenant."""
        # Verify tenant exists
        tenant = await TenantService.get_tenant_by_id(db, seat_data.tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        # Create seats
        seats = []
        for _ in range(seat_data.count):
            seat = Seat(tenant_id=seat_data.tenant_id, state=SeatState.FREE)
            db.add(seat)
            seats.append(seat)

        await db.flush()  # Get IDs before commit

        # Create audit entries for seat creation
        for seat in seats:
            audit_entry = SeatAudit(
                seat_id=seat.id,
                previous_state=None,
                new_state=SeatState.FREE,
                previous_learner_id=None,
                new_learner_id=None,
                changed_by=user_id,
                reason="Seat purchased"
            )
            db.add(audit_entry)

        await db.commit()
        
        # Refresh all seats
        for seat in seats:
            await db.refresh(seat)
        
        return seats

    @staticmethod
    async def allocate_seat(
        db: AsyncSession, 
        allocation_data: SeatAllocate, 
        user_id: str
    ) -> Seat:
        """Allocate a seat to a learner."""
        # Get seat and verify it's available
        seat = await SeatService.get_seat_by_id(db, allocation_data.seat_id)
        if not seat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat not found"
            )
        
        if seat.state != SeatState.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Seat is not available. Current state: {seat.state}"
            )

        # Check if learner already has a seat in this tenant
        existing_seat = await SeatService.get_learner_seat_in_tenant(
            db, allocation_data.learner_id, seat.tenant_id
        )
        if existing_seat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Learner already has a seat in this tenant"
            )

        # Update seat
        previous_state = seat.state
        previous_learner_id = seat.learner_id
        
        seat.state = SeatState.ASSIGNED
        seat.learner_id = allocation_data.learner_id
        seat.assigned_at = datetime.now(timezone.utc)

        # Create audit entry
        audit_entry = SeatAudit(
            seat_id=seat.id,
            previous_state=previous_state,
            new_state=seat.state,
            previous_learner_id=previous_learner_id,
            new_learner_id=seat.learner_id,
            changed_by=user_id,
            reason="Seat allocated to learner"
        )
        db.add(audit_entry)

        await db.commit()
        await db.refresh(seat)
        return seat

    @staticmethod
    async def reclaim_seat(
        db: AsyncSession, 
        reclaim_data: SeatReclaim, 
        user_id: str
    ) -> Seat:
        """Reclaim a seat from a learner."""
        seat = await SeatService.get_seat_by_id(db, reclaim_data.seat_id)
        if not seat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seat not found"
            )

        if seat.state == SeatState.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seat is already free"
            )

        # Update seat
        previous_state = seat.state
        previous_learner_id = seat.learner_id
        
        seat.state = SeatState.FREE
        seat.learner_id = None
        seat.reserved_at = None
        seat.assigned_at = None

        # Create audit entry
        audit_entry = SeatAudit(
            seat_id=seat.id,
            previous_state=previous_state,
            new_state=seat.state,
            previous_learner_id=previous_learner_id,
            new_learner_id=None,
            changed_by=user_id,
            reason=reclaim_data.reason or "Seat reclaimed"
        )
        db.add(audit_entry)

        await db.commit()
        await db.refresh(seat)
        return seat

    @staticmethod
    async def get_seat_by_id(db: AsyncSession, seat_id: int) -> Optional[Seat]:
        """Get seat by ID."""
        result = await db.execute(
            select(Seat).where(Seat.id == seat_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_learner_seat_in_tenant(
        db: AsyncSession, 
        learner_id: str, 
        tenant_id: int
    ) -> Optional[Seat]:
        """Check if learner already has a seat in the tenant."""
        result = await db.execute(
            select(Seat).where(
                and_(
                    Seat.learner_id == learner_id,
                    Seat.tenant_id == tenant_id,
                    Seat.state.in_([SeatState.RESERVED, SeatState.ASSIGNED])
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_seat_summary(db: AsyncSession, tenant_id: int) -> Optional[SeatSummary]:
        """Get seat allocation summary for a tenant."""
        tenant = await TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            return None

        # Get seat counts by state
        result = await db.execute(
            select(
                Seat.state,
                func.count(Seat.id).label('count')
            )
            .where(Seat.tenant_id == tenant_id)
            .group_by(Seat.state)
        )
        
        counts = {row.state: row.count for row in result}
        
        total_seats = sum(counts.values())
        free_seats = counts.get(SeatState.FREE, 0)
        reserved_seats = counts.get(SeatState.RESERVED, 0)
        assigned_seats = counts.get(SeatState.ASSIGNED, 0)
        
        utilization_percentage = (
            ((reserved_seats + assigned_seats) / total_seats * 100) 
            if total_seats > 0 else 0
        )

        return SeatSummary(
            tenant_id=tenant_id,
            tenant_name=tenant.name,
            total_seats=total_seats,
            free_seats=free_seats,
            reserved_seats=reserved_seats,
            assigned_seats=assigned_seats,
            utilization_percentage=round(utilization_percentage, 2)
        )


class UserRoleService:
    """Service for managing user roles within tenants."""

    @staticmethod
    async def assign_user_role(
        db: AsyncSession, 
        role_data: UserTenantRoleCreate
    ) -> UserTenantRole:
        """Assign a role to a user within a tenant."""
        # Verify tenant exists
        tenant = await TenantService.get_tenant_by_id(db, role_data.tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        # Check if user already has a role in this tenant
        existing_role = await UserRoleService.get_user_role(
            db, role_data.user_id, role_data.tenant_id
        )
        if existing_role and existing_role.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active role in this tenant"
            )

        user_role = UserTenantRole(**role_data.model_dump())
        db.add(user_role)
        await db.commit()
        await db.refresh(user_role)
        return user_role

    @staticmethod
    async def get_user_role(
        db: AsyncSession, 
        user_id: str, 
        tenant_id: int
    ) -> Optional[UserTenantRole]:
        """Get user's role in a specific tenant."""
        result = await db.execute(
            select(UserTenantRole).where(
                and_(
                    UserTenantRole.user_id == user_id,
                    UserTenantRole.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_tenants(db: AsyncSession, user_id: str) -> List[UserTenantRole]:
        """Get all tenants where user has roles."""
        result = await db.execute(
            select(UserTenantRole)
            .options(selectinload(UserTenantRole.tenant))
            .where(
                and_(
                    UserTenantRole.user_id == user_id,
                    UserTenantRole.is_active == True
                )
            )
        )
        return list(result.scalars().all())
