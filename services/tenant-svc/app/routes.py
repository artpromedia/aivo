"""
API routes for tenant service.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_database
from .schemas import (
    DistrictCreate,
    MessageResponse,
    SchoolCreate,
    Seat,
    SeatAllocate,
    SeatCreate,
    SeatReclaim,
    SeatSummary,
    Tenant,
    TenantUpdate,
    TenantWithChildren,
    UserTenantRole,
    UserTenantRoleCreate,
)
from .services import SeatService, TenantService, UserRoleService

router = APIRouter()


def get_current_user_id(x_user_id: str = Header(..., description="Current user ID")) -> str:
    """Get current user ID from headers (simplified for this implementation)."""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID header required"
        )
    return x_user_id


# District routes
@router.post("/district", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_district(
    district_data: DistrictCreate,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Create a new district."""
    try:
        district = await TenantService.create_district(db, district_data)
        return district
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create district: {str(e)}",
        )


@router.get("/district/{district_id}", response_model=TenantWithChildren)
async def get_district(
    district_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Get a district with its schools."""
    district = await TenantService.get_district_with_schools(db, district_id)
    if not district:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="District not found")
    return district


@router.post(
    "/district/{district_id}/schools", response_model=Tenant, status_code=status.HTTP_201_CREATED
)
async def create_school(
    district_id: int,
    school_data: SchoolCreate,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Create a new school under a district."""
    try:
        school = await TenantService.create_school(db, district_id, school_data)
        return school
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create school: {str(e)}",
        )


# Tenant routes
@router.get("/tenant/{tenant_id}", response_model=Tenant)
async def get_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Get tenant by ID."""
    tenant = await TenantService.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


@router.put("/tenant/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Update tenant information."""
    tenant = await TenantService.update_tenant(db, tenant_id, tenant_data)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


# Seat routes
@router.post("/seats/purchase", response_model=list[Seat], status_code=status.HTTP_201_CREATED)
async def purchase_seats(
    seat_data: SeatCreate,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Purchase (create) seats for a tenant."""
    try:
        seats = await SeatService.purchase_seats(db, seat_data, current_user)
        return seats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purchase seats: {str(e)}",
        )


@router.post("/seats/allocate", response_model=Seat)
async def allocate_seat(
    allocation_data: SeatAllocate,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Allocate a seat to a learner."""
    try:
        seat = await SeatService.allocate_seat(db, allocation_data, current_user)
        return seat
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to allocate seat: {str(e)}",
        )


@router.post("/seats/reclaim", response_model=Seat)
async def reclaim_seat(
    reclaim_data: SeatReclaim,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Reclaim a seat from a learner."""
    try:
        seat = await SeatService.reclaim_seat(db, reclaim_data, current_user)
        return seat
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reclaim seat: {str(e)}",
        )


@router.get("/seats/summary", response_model=SeatSummary)
async def get_seat_summary(
    tenantId: int,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Get seat allocation summary for a tenant."""
    summary = await SeatService.get_seat_summary(db, tenantId)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return summary


@router.get("/seats/{seat_id}", response_model=Seat)
async def get_seat(
    seat_id: int,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Get seat by ID."""
    seat = await SeatService.get_seat_by_id(db, seat_id)
    if not seat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found")
    return seat


# User role routes
@router.post("/roles", response_model=UserTenantRole, status_code=status.HTTP_201_CREATED)
async def assign_user_role(
    role_data: UserTenantRoleCreate,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Assign a role to a user within a tenant."""
    try:
        user_role = await UserRoleService.assign_user_role(db, role_data)
        return user_role
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign role: {str(e)}",
        )


@router.get("/users/{user_id}/tenants", response_model=list[UserTenantRole])
async def get_user_tenants(
    user_id: str,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Get all tenants where user has roles."""
    user_roles = await UserRoleService.get_user_tenants(db, user_id)
    return user_roles


# Health check
@router.get("/health", response_model=MessageResponse)
async def health_check():
    """Health check endpoint."""
    return MessageResponse(message="Tenant service is healthy")


# Add roles listing endpoint
@router.get("/roles", response_model=list[UserTenantRole])
async def get_roles(
    tenantId: int,
    db: AsyncSession = Depends(get_database),
    current_user: str = Depends(get_current_user_id),
):
    """Get all user roles for a specific tenant."""
    try:
        roles = await UserRoleService.get_tenant_roles(db, tenantId)
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get roles: {str(e)}",
        )
