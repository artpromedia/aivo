"""
FastAPI application for enrollment router service.
"""
import logging
from contextlib import asynccontextmanager
from typing import List, Union

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db, create_tables
from .models import DistrictSeatAllocation, EnrollmentDecision
from .schemas import (
    EnrollmentRequest, EnrollmentDecisionResponse,
    DistrictSeatAllocationCreate, DistrictSeatAllocationUpdate, 
    DistrictSeatAllocationResponse, DistrictEnrollmentResult,
    ParentEnrollmentResult
)
from .services import EnrollmentRouterService, DistrictSeatService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await create_tables()
    logger.info("Enrollment Router Service started")
    yield
    # Shutdown
    logger.info("Enrollment Router Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Enrollment Router Service",
    description="Routes learner enrollments between district and parent provisioning",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
enrollment_service = EnrollmentRouterService()
district_service = DistrictSeatService()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "enrollment-router"}


@app.post("/enroll", response_model=Union[DistrictEnrollmentResult, ParentEnrollmentResult])
async def enroll_learner(
    request: EnrollmentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Route learner enrollment based on context and availability.
    
    - If context.tenant_id & FREE seats → reserve, set provision_source='district'
    - Else → provision_source='parent' + return checkout URL
    """
    try:
        result = await enrollment_service.route_enrollment(db, request)
        logger.info(
            f"Enrollment routed: {request.learner_profile.email} -> "
            f"{result.provision_source.value}"
        )
        return result
    except Exception as e:
        logger.error(f"Enrollment routing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrollment routing failed: {str(e)}"
        )


@app.get("/enrollments/{decision_id}", response_model=EnrollmentDecisionResponse)
async def get_enrollment_decision(
    decision_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get enrollment decision by ID."""
    result = await db.execute(
        select(EnrollmentDecision).where(EnrollmentDecision.id == decision_id)
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment decision not found"
        )
    
    return EnrollmentDecisionResponse(
        decision_id=decision.id,
        provision_source=decision.provision_source,
        status=decision.status,
        learner_profile=decision.learner_profile,
        context=decision.context,
        tenant_id=decision.tenant_id,
        seats_reserved=decision.district_seats_reserved,
        seats_available=decision.district_seats_available,
        guardian_id=decision.guardian_id,
        checkout_session_id=decision.checkout_session_id,
        checkout_url=decision.checkout_url,
        created_at=decision.created_at,
        message=decision.error_message or "Success"
    )


@app.get("/enrollments", response_model=List[EnrollmentDecisionResponse])
async def list_enrollment_decisions(
    tenant_id: int = None,
    guardian_id: str = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List enrollment decisions with optional filtering."""
    query = select(EnrollmentDecision)
    
    if tenant_id:
        query = query.where(EnrollmentDecision.tenant_id == tenant_id)
    if guardian_id:
        query = query.where(EnrollmentDecision.guardian_id == guardian_id)
    
    query = query.offset(offset).limit(limit).order_by(EnrollmentDecision.created_at.desc())
    
    result = await db.execute(query)
    decisions = result.scalars().all()
    
    return [
        EnrollmentDecisionResponse(
            decision_id=decision.id,
            provision_source=decision.provision_source,
            status=decision.status,
            learner_profile=decision.learner_profile,
            context=decision.context,
            tenant_id=decision.tenant_id,
            seats_reserved=decision.district_seats_reserved,
            seats_available=decision.district_seats_available,
            guardian_id=decision.guardian_id,
            checkout_session_id=decision.checkout_session_id,
            checkout_url=decision.checkout_url,
            created_at=decision.created_at,
            message=decision.error_message or "Success"
        )
        for decision in decisions
    ]


# District seat management endpoints
@app.post("/districts/seats", response_model=DistrictSeatAllocationResponse)
async def create_district_allocation(
    allocation: DistrictSeatAllocationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create district seat allocation."""
    try:
        result = await district_service.create_allocation(
            db, allocation.tenant_id, allocation.total_seats
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create district allocation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create allocation: {str(e)}"
        )


@app.get("/districts/{tenant_id}/seats", response_model=DistrictSeatAllocationResponse)
async def get_district_allocation(
    tenant_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get district seat allocation."""
    allocation = await district_service.get_allocation(db, tenant_id)
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="District allocation not found"
        )
    return allocation


@app.put("/districts/{tenant_id}/seats", response_model=DistrictSeatAllocationResponse)
async def update_district_allocation(
    tenant_id: int,
    update: DistrictSeatAllocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update district seat allocation."""
    allocation = await district_service.get_allocation(db, tenant_id)
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="District allocation not found"
        )
    
    if update.total_seats is not None:
        allocation.total_seats = update.total_seats
    if update.is_active is not None:
        allocation.is_active = update.is_active
    
    await db.commit()
    await db.refresh(allocation)
    return allocation


@app.get("/districts", response_model=List[DistrictSeatAllocationResponse])
async def list_district_allocations(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all district seat allocations."""
    query = select(DistrictSeatAllocation)
    if active_only:
        query = query.where(DistrictSeatAllocation.is_active == True)
    
    result = await db.execute(query)
    allocations = result.scalars().all()
    return allocations


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
