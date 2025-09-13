from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import (
    SLAPolicy,
    SLAPolicyCreate, SLAPolicyResponse,
    TicketPriority
)

router = APIRouter(prefix="/sla", tags=["sla"])

@router.get("/policies", response_model=List[SLAPolicyResponse])
async def get_sla_policies(db: AsyncSession = Depends(get_db)):
    """Get all SLA policies"""

    result = await db.execute(
        select(SLAPolicy).order_by(SLAPolicy.priority, SLAPolicy.created_at.desc())
    )
    policies = result.scalars().all()

    return policies

@router.get("/policies/{policy_id}", response_model=SLAPolicyResponse)
async def get_sla_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific SLA policy by ID"""

    result = await db.execute(select(SLAPolicy).where(SLAPolicy.id == policy_id))
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=404, detail="SLA policy not found")

    return policy

@router.post("/policies", response_model=SLAPolicyResponse)
async def create_sla_policy(policy_data: SLAPolicyCreate, db: AsyncSession = Depends(get_db)):
    """Create a new SLA policy"""

    # Check if policy already exists for this priority
    existing_result = await db.execute(
        select(SLAPolicy).where(
            SLAPolicy.priority == policy_data.priority.value,
            SLAPolicy.is_active == True
        )
    )
    existing_policy = existing_result.scalar_one_or_none()

    if existing_policy:
        # Deactivate existing policy
        existing_policy.is_active = False

    policy = SLAPolicy(
        name=policy_data.name,
        priority=policy_data.priority.value,
        response_time_hours=policy_data.response_time_hours,
        resolution_time_hours=policy_data.resolution_time_hours,
        is_active=policy_data.is_active
    )

    db.add(policy)
    await db.commit()
    await db.refresh(policy)

    return policy

@router.put("/policies/{policy_id}", response_model=SLAPolicyResponse)
async def update_sla_policy(
    policy_id: int,
    policy_data: SLAPolicyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update an SLA policy"""

    result = await db.execute(select(SLAPolicy).where(SLAPolicy.id == policy_id))
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=404, detail="SLA policy not found")

    policy.name = policy_data.name
    policy.priority = policy_data.priority.value
    policy.response_time_hours = policy_data.response_time_hours
    policy.resolution_time_hours = policy_data.resolution_time_hours
    policy.is_active = policy_data.is_active

    await db.commit()
    await db.refresh(policy)

    return policy

@router.delete("/policies/{policy_id}")
async def delete_sla_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an SLA policy"""

    result = await db.execute(select(SLAPolicy).where(SLAPolicy.id == policy_id))
    policy = result.scalar_one_or_none()

    if not policy:
        raise HTTPException(status_code=404, detail="SLA policy not found")

    await db.delete(policy)
    await db.commit()

    return {"message": "SLA policy deleted successfully"}

@router.post("/policies/seed")
async def seed_default_sla_policies(db: AsyncSession = Depends(get_db)):
    """Seed default SLA policies"""

    default_policies = [
        {
            "name": "Critical Issues",
            "priority": TicketPriority.CRITICAL.value,
            "response_time_hours": 1,
            "resolution_time_hours": 4
        },
        {
            "name": "High Priority Issues",
            "priority": TicketPriority.HIGH.value,
            "response_time_hours": 2,
            "resolution_time_hours": 8
        },
        {
            "name": "Medium Priority Issues",
            "priority": TicketPriority.MEDIUM.value,
            "response_time_hours": 4,
            "resolution_time_hours": 24
        },
        {
            "name": "Low Priority Issues",
            "priority": TicketPriority.LOW.value,
            "response_time_hours": 8,
            "resolution_time_hours": 72
        }
    ]

    created_policies = []
    for policy_data in default_policies:
        # Check if policy already exists
        existing_result = await db.execute(
            select(SLAPolicy).where(SLAPolicy.priority == policy_data["priority"])
        )
        existing_policy = existing_result.scalar_one_or_none()

        if not existing_policy:
            policy = SLAPolicy(**policy_data)
            db.add(policy)
            created_policies.append(policy_data["name"])

    await db.commit()

    return {"message": f"Created {len(created_policies)} default SLA policies", "policies": created_policies}
