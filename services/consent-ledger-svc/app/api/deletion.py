"""
Data deletion API endpoints.

GDPR Article 17 compliant cascaded data deletion across all systems.
"""

from datetime import datetime
from uuid import UUID

from config import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeletionStatus
from app.services import CascadeDeleteService
from app.tasks import process_data_deletion

router = APIRouter()


# Request/Response models
class DeletionRequest(BaseModel):
    """Request model for data deletion."""

    user_id: str = Field(..., description="User identifier")
    reason: str = Field(..., description="Deletion reason")
    requested_by: str = Field(..., description="Who requested deletion")
    include_audit_logs: bool = Field(False, description="Include audit logs in deletion")
    metadata: dict | None = Field(None, description="Additional metadata")

    @validator("user_id", "reason", "requested_by")
    def validate_not_empty(self, v):
        """Validate non-empty fields."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Field cannot be empty")
        return v.strip()


class DeletionResponse(BaseModel):
    """Response model for deletion requests."""

    id: UUID
    user_id: str
    status: DeletionStatus
    reason: str
    requested_by: str
    total_systems: int
    completed_systems: int
    failed_systems: int
    verification_required: bool
    verification_deadline: datetime | None
    created_at: datetime
    completed_at: datetime | None
    progress_percentage: int

    class Config:
        from_attributes = True


class DeletionListResponse(BaseModel):
    """Response model for deletion list."""

    deletions: list[DeletionResponse]
    total: int
    page: int
    per_page: int


class SystemDeletionStatus(BaseModel):
    """Status of deletion for a specific system."""

    system_name: str
    status: str
    records_deleted: int | None
    error_message: str | None
    completed_at: datetime | None


def get_cascade_delete_service(db: AsyncSession = Depends(get_db)) -> CascadeDeleteService:
    """Get cascade delete service instance."""
    return CascadeDeleteService(db)


@router.post("/", response_model=DeletionResponse, status_code=201)
async def create_deletion_request(
    request: DeletionRequest,
    background_tasks: BackgroundTasks,
    delete_service: CascadeDeleteService = Depends(get_cascade_delete_service),
):
    """
    Create a new data deletion request.

    Initiates GDPR Article 17 cascaded deletion across all systems.
    """
    try:
        deletion_request = await delete_service.create_deletion_request(
            user_id=request.user_id,
            reason=request.reason,
            requested_by=request.requested_by,
            include_audit_logs=request.include_audit_logs,
            metadata=request.metadata or {},
        )

        # Start background processing
        background_tasks.add_task(process_data_deletion.delay, str(deletion_request.id))

        return DeletionResponse.from_orm(deletion_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create deletion request")


@router.get("/user/{user_id}", response_model=DeletionListResponse)
async def get_user_deletions(
    user_id: str,
    status: DeletionStatus | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    delete_service: CascadeDeleteService = Depends(get_cascade_delete_service),
):
    """
    Get deletion requests for a user.

    Returns paginated list of deletion requests with optional status filtering.
    """
    try:
        deletions, total = await delete_service.get_user_deletions(
            user_id=user_id, status=status, limit=per_page, offset=(page - 1) * per_page
        )

        return DeletionListResponse(
            deletions=[DeletionResponse.from_orm(d) for d in deletions],
            total=total,
            page=page,
            per_page=per_page,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve deletions")


@router.get("/{deletion_id}", response_model=DeletionResponse)
async def get_deletion_request(
    deletion_id: UUID, delete_service: CascadeDeleteService = Depends(get_cascade_delete_service)
):
    """
    Get specific deletion request by ID.

    Returns detailed deletion information including system-level progress.
    """
    try:
        deletion = await delete_service.get_deletion_request(deletion_id)
        if not deletion:
            raise HTTPException(status_code=404, detail="Deletion request not found")

        return DeletionResponse.from_orm(deletion)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve deletion")


@router.get("/{deletion_id}/systems")
async def get_deletion_system_status(
    deletion_id: UUID, delete_service: CascadeDeleteService = Depends(get_cascade_delete_service)
):
    """
    Get deletion status for each system.

    Returns detailed status of deletion across all integrated systems.
    """
    try:
        deletion = await delete_service.get_deletion_request(deletion_id)
        if not deletion:
            raise HTTPException(status_code=404, detail="Deletion request not found")

        system_statuses = await delete_service.get_system_deletion_status(deletion_id)

        return {
            "deletion_id": str(deletion_id),
            "user_id": deletion.user_id,
            "overall_status": deletion.status,
            "systems": [
                SystemDeletionStatus(
                    system_name=status["system_name"],
                    status=status["status"],
                    records_deleted=status.get("records_deleted"),
                    error_message=status.get("error_message"),
                    completed_at=status.get("completed_at"),
                )
                for status in system_statuses
            ],
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.post("/{deletion_id}/verify", status_code=204)
async def verify_deletion_request(
    deletion_id: UUID,
    verification_code: str = Query(..., description="Verification code"),
    delete_service: CascadeDeleteService = Depends(get_cascade_delete_service),
):
    """
    Verify deletion request with verification code.

    Confirms deletion request before proceeding with actual deletion.
    """
    try:
        success = await delete_service.verify_deletion_request(deletion_id, verification_code)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid verification code or request")

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to verify deletion")


@router.delete("/{deletion_id}", status_code=204)
async def cancel_deletion_request(
    deletion_id: UUID, delete_service: CascadeDeleteService = Depends(get_cascade_delete_service)
):
    """
    Cancel pending deletion request.

    Cancels deletion if still pending or in progress.
    """
    try:
        success = await delete_service.cancel_deletion_request(deletion_id)
        if not success:
            raise HTTPException(
                status_code=404, detail="Deletion request not found or cannot be cancelled"
            )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to cancel deletion")


@router.get("/")
async def list_all_deletions(
    status: DeletionStatus | None = Query(None, description="Filter by status"),
    verification_pending: bool = Query(False, description="Show only pending verification"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    delete_service: CascadeDeleteService = Depends(get_cascade_delete_service),
):
    """
    List all deletion requests (admin endpoint).

    Returns paginated list of all deletion requests with filtering options.
    """
    try:
        deletions, total = await delete_service.list_all_deletions(
            status=status,
            verification_pending=verification_pending,
            limit=per_page,
            offset=(page - 1) * per_page,
        )

        return DeletionListResponse(
            deletions=[DeletionResponse.from_orm(d) for d in deletions],
            total=total,
            page=page,
            per_page=per_page,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list deletions")


@router.get("/stats/summary")
async def get_deletion_statistics(
    delete_service: CascadeDeleteService = Depends(get_cascade_delete_service),
):
    """
    Get deletion statistics and metrics.

    Returns summary of deletion requests by status and system performance.
    """
    try:
        stats = await delete_service.get_deletion_statistics()
        return stats
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get deletion statistics")


@router.post("/{deletion_id}/retry", response_model=DeletionResponse)
async def retry_failed_deletion(
    deletion_id: UUID,
    background_tasks: BackgroundTasks,
    systems: list[str] | None = Query(None, description="Specific systems to retry"),
    delete_service: CascadeDeleteService = Depends(get_cascade_delete_service),
):
    """
    Retry failed deletion request.

    Resets failed deletion to pending and starts processing again.
    """
    try:
        deletion = await delete_service.retry_deletion_request(deletion_id, systems)
        if not deletion:
            raise HTTPException(status_code=404, detail="Deletion request not found or not failed")

        # Start background processing
        background_tasks.add_task(process_data_deletion.delay, str(deletion.id))

        return DeletionResponse.from_orm(deletion)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retry deletion")


@router.post("/bulk", response_model=list[DeletionResponse])
async def create_bulk_deletion(
    user_ids: list[str] = Field(..., description="List of user IDs to delete"),
    reason: str = Field(..., description="Deletion reason"),
    requested_by: str = Field(..., description="Who requested deletion"),
    background_tasks: BackgroundTasks = None,
    delete_service: CascadeDeleteService = Depends(get_cascade_delete_service),
):
    """
    Create bulk deletion requests.

    Creates multiple deletion requests for batch processing.
    """
    try:
        if len(user_ids) > 100:  # Limit bulk operations
            raise HTTPException(status_code=400, detail="Maximum 100 users per bulk deletion")

        deletions = await delete_service.create_bulk_deletion_requests(
            user_ids=user_ids, reason=reason, requested_by=requested_by
        )

        # Start background processing for each
        for deletion in deletions:
            background_tasks.add_task(process_data_deletion.delay, str(deletion.id))

        return [DeletionResponse.from_orm(d) for d in deletions]
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create bulk deletions")
