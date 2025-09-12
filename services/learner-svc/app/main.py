"""
FastAPI application for learner service.
"""

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import create_tables, get_db
from .schemas import (
    ErrorResponse,
    Guardian,
    GuardianCreate,
    HealthResponse,
    Learner,
    LearnerCreate,
    LearnerResponse,
    LearnerTeacherBulkAssignment,
    LearnerUpdate,
    Teacher,
    TeacherAssignment,
    TeacherCreate,
    Tenant,
    TenantCreate,
)
from .services import (
    GuardianService,
    LearnerService,
    TeacherService,
    TenantService,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting learner service...")
    await create_tables()
    yield
    # Shutdown
    logger.info("Shutting down learner service...")


# Create FastAPI app
app = FastAPI(
    title="Learner Service",
    description=("Manages learners with guardian-first approach " "and teacher relationships"),
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy", service="learner-svc", version="1.0.0", timestamp=datetime.now(UTC)
    )


# Guardian endpoints
@app.post("/guardians", response_model=Guardian, status_code=status.HTTP_201_CREATED)
async def create_guardian(guardian_data: GuardianCreate, db: AsyncSession = Depends(get_db)):
    """Create a new guardian."""
    try:
        service = GuardianService(db)
        guardian = await service.create_guardian(guardian_data)
        return guardian
    except Exception as e:
        logger.error("Failed to create guardian: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create guardian: {str(e)}"
        ) from e


@app.get("/guardians/{guardian_id}", response_model=Guardian)
async def get_guardian(guardian_id: int, db: AsyncSession = Depends(get_db)):
    """Get guardian by ID."""
    service = GuardianService(db)
    guardian = await service.get_guardian(guardian_id)

    if not guardian:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guardian with ID {guardian_id} not found",
        )

    return guardian


# Tenant endpoints
@app.post("/tenants", response_model=Tenant, status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant_data: TenantCreate, db: AsyncSession = Depends(get_db)):
    """Create a new tenant."""
    try:
        service = TenantService(db)
        tenant = await service.create_tenant(tenant_data)
        return tenant
    except Exception as e:
        logger.error("Failed to create tenant: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create tenant: {str(e)}"
        ) from e


@app.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: int, db: AsyncSession = Depends(get_db)):
    """Get tenant by ID."""
    service = TenantService(db)
    tenant = await service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with ID {tenant_id} not found"
        )

    return tenant


# Teacher endpoints
@app.post("/teachers", response_model=Teacher, status_code=status.HTTP_201_CREATED)
async def create_teacher(teacher_data: TeacherCreate, db: AsyncSession = Depends(get_db)):
    """Create a new teacher."""
    try:
        service = TeacherService(db)
        teacher = await service.create_teacher(teacher_data)
        return teacher
    except Exception as e:
        logger.error("Failed to create teacher: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create teacher: {str(e)}"
        ) from e


@app.get("/teachers/{teacher_id}", response_model=Teacher)
async def get_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    """Get teacher by ID."""
    service = TeacherService(db)
    teacher = await service.get_teacher(teacher_id)

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Teacher with ID {teacher_id} not found"
        )

    return teacher


# Learner endpoints
@app.post("/learners", response_model=Learner, status_code=status.HTTP_201_CREATED)
async def create_learner(
    learner_data: LearnerCreate,
    _background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new learner with guardian-first approach."""
    try:
        service = LearnerService(db)
        learner = await service.create_learner(learner_data)

        # Return learner with full relations
        learner_with_relations = await service.get_learner(learner.id, include_relations=True)
        return learner_with_relations

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to create learner: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create learner: {str(e)}",
        ) from e


@app.get("/learners/{learner_id}", response_model=Learner)
async def get_learner(
    learner_id: int, include_relations: bool = True, db: AsyncSession = Depends(get_db)
):
    """Get learner by ID."""
    service = LearnerService(db)
    learner = await service.get_learner(learner_id, include_relations=include_relations)

    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Learner with ID {learner_id} not found"
        )

    return learner


@app.get("/guardians/{guardian_id}/learners", response_model=list[Learner])
async def get_learners_by_guardian(guardian_id: int, db: AsyncSession = Depends(get_db)):
    """Get all learners for a guardian."""
    service = LearnerService(db)
    learners = await service.get_learners_by_guardian(guardian_id)
    return learners


@app.put("/learners/{learner_id}", response_model=LearnerResponse)
async def update_learner(
    learner_id: int, update_data: LearnerUpdate, db: AsyncSession = Depends(get_db)
):
    """Update an existing learner."""
    try:
        result = await db.execute(
            select(Learner)
            .options(
                selectinload(Learner.guardian),
                selectinload(Learner.tenant),
                selectinload(Learner.teachers),
            )
            .where(Learner.id == learner_id)
        )
        learner = result.scalar_one_or_none()

        if not learner:
            raise HTTPException(status_code=404, detail="Learner not found")

        # Update fields
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(learner, field, value)

        await db.commit()
        await db.refresh(learner)

        # Reload with relationships
        result = await db.execute(
            select(Learner)
            .options(
                selectinload(Learner.guardian),
                selectinload(Learner.tenant),
                selectinload(Learner.teachers),
            )
            .where(Learner.id == learner_id)
        )
        updated_learner = result.scalar_one()

        return updated_learner

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update learner %s: %s", learner_id, str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update learner") from e


# Teacher assignment endpoints
@app.post("/learners/{learner_id}/teachers", status_code=201)
async def assign_teacher_to_learner(
    learner_id: int, assignment: TeacherAssignment, db: AsyncSession = Depends(get_db)
):
    """Assign a teacher to a learner."""
    learner_service = LearnerService(db)

    try:
        await learner_service.assign_teacher(
            learner_id=learner_id,
            teacher_id=assignment.teacher_id,
            assigned_by=assignment.assigned_by,
        )
        return {
            "message": (f"Teacher {assignment.teacher_id} assigned to " f"learner {learner_id}")
        }

    except ValueError as e:
        error_msg = str(e)
        if "already assigned" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg) from e
        elif "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg) from e
        else:
            raise HTTPException(status_code=400, detail=error_msg) from e
    except Exception as e:
        logger.error("Failed to assign teacher: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to assign teacher") from e


@app.post("/learners/{learner_id}/teachers/bulk", status_code=status.HTTP_201_CREATED)
async def assign_multiple_teachers_to_learner(
    learner_id: int, assignment: LearnerTeacherBulkAssignment, db: AsyncSession = Depends(get_db)
):
    """Assign multiple teachers to a learner."""
    try:
        service = LearnerService(db)
        results = await service.assign_multiple_teachers(
            learner_id, assignment.teacher_ids, assignment.assigned_by
        )

        successful_assignments = [tid for tid, success in results.items() if success]
        failed_assignments = [tid for tid, success in results.items() if not success]

        return {
            "message": (f"Teacher assignment completed for learner {learner_id}"),
            "successful_assignments": successful_assignments,
            "failed_assignments": failed_assignments,
            "total_requested": len(assignment.teacher_ids),
            "total_successful": len(successful_assignments),
        }

    except Exception as e:
        logger.error("Failed to assign teachers: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign teachers: {str(e)}",
        ) from e


@app.delete("/learners/{learner_id}/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_teacher_from_learner(
    learner_id: int, teacher_id: int, db: AsyncSession = Depends(get_db)
):
    """Remove a teacher assignment from a learner."""
    try:
        service = LearnerService(db)
        success = await service.remove_teacher(learner_id, teacher_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No assignment found between teacher {teacher_id} " f"and learner {learner_id}"
                ),
            )

    except Exception as e:
        logger.error("Failed to remove teacher assignment: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove teacher assignment: {str(e)}",
        ) from e


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError) -> ErrorResponse:
    """Handle ValueError exceptions."""
    return ErrorResponse(error="Validation Error", detail=str(exc), timestamp=datetime.utcnow())


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception) -> ErrorResponse:
    """Handle general exceptions."""
    logger.error("Unhandled exception: %s", str(exc))
    return ErrorResponse(
        error="Server Error",
        message=f"An unexpected error occurred: {exc}",
        timestamp=datetime.now(UTC),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
