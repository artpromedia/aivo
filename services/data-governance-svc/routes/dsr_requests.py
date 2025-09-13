"""
Data Subject Rights (DSR) API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from ..models import DSRType, DSRStatus, EntityType
from ..schemas.dsr import (
    DSRRequestCreate, DSRRequestResponse, DSRRequestListResponse,
    DSRStatusResponse, DSRExportResponse
)
from ..services.dsr_service import DSRService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/export", response_model=DSRRequestResponse)
@limiter.limit("5/minute")
async def create_export_request(
    request,
    export_request: DSRRequestCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a data export request for a subject."""
    service = DSRService(db)

    # Validate request
    if export_request.dsr_type != DSRType.EXPORT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request type must be 'export' for this endpoint"
        )

    # Create DSR request
    dsr_request = await service.create_request(export_request)

    # Start background export process
    background_tasks.add_task(
        service.process_export_request,
        dsr_request.id
    )

    return dsr_request


@router.post("/delete", response_model=DSRRequestResponse)
@limiter.limit("3/minute")
async def create_delete_request(
    request,
    delete_request: DSRRequestCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a data deletion request for a subject."""
    service = DSRService(db)

    # Validate request
    if delete_request.dsr_type != DSRType.DELETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request type must be 'delete' for this endpoint"
        )

    # Create DSR request
    dsr_request = await service.create_request(delete_request)

    # Start background deletion process
    background_tasks.add_task(
        service.process_delete_request,
        dsr_request.id
    )

    return dsr_request


@router.get("/requests", response_model=DSRRequestListResponse)
@limiter.limit("30/minute")
async def list_dsr_requests(
    request,
    dsr_type: Optional[DSRType] = Query(None, description="Filter by DSR type"),
    status_filter: Optional[DSRStatus] = Query(None, alias="status", description="Filter by status"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of requests to return"),
    offset: int = Query(0, ge=0, description="Number of requests to skip"),
    db: AsyncSession = Depends(get_db)
):
    """List DSR requests with filtering and pagination."""
    service = DSRService(db)

    requests, total = await service.list_requests(
        dsr_type=dsr_type,
        status=status_filter,
        subject_id=subject_id,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset
    )

    return DSRRequestListResponse(
        requests=requests,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/requests/{request_id}", response_model=DSRRequestResponse)
@limiter.limit("30/minute")
async def get_dsr_request(
    request,
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific DSR request by ID."""
    service = DSRService(db)

    dsr_request = await service.get_request(request_id)
    if not dsr_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DSR request not found"
        )

    return dsr_request


@router.get("/requests/{request_id}/status", response_model=DSRStatusResponse)
@limiter.limit("60/minute")
async def get_dsr_status(
    request,
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get processing status of DSR request."""
    service = DSRService(db)

    status_info = await service.get_request_status(request_id)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DSR request not found"
        )

    return status_info


@router.get("/requests/{request_id}/download")
@limiter.limit("10/minute")
async def download_export(
    request,
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Download export file for completed export request."""
    service = DSRService(db)

    download_response = await service.get_export_download(request_id)
    return download_response


@router.post("/requests/{request_id}/verify")
@limiter.limit("10/minute")
async def verify_identity(
    request,
    request_id: str,
    verification_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify identity for DSR request processing."""
    service = DSRService(db)

    success = await service.verify_identity(request_id, verification_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token or request not found"
        )

    return {"message": "Identity verified successfully"}


@router.delete("/requests/{request_id}")
@limiter.limit("5/minute")
async def cancel_dsr_request(
    request,
    request_id: str,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    db: AsyncSession = Depends(get_db)
):
    """Cancel pending DSR request."""
    service = DSRService(db)

    success = await service.cancel_request(request_id, reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DSR request not found or cannot be cancelled"
        )

    return {"message": "DSR request cancelled successfully"}


@router.post("/bulk-export")
@limiter.limit("2/minute")
async def bulk_export_request(
    request,
    subject_ids: List[str],
    subject_type: EntityType,
    requester_email: str,
    tenant_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """Create bulk export requests for multiple subjects."""
    service = DSRService(db)

    if len(subject_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 subjects allowed per bulk request"
        )

    requests = await service.create_bulk_export_requests(
        subject_ids=subject_ids,
        subject_type=subject_type,
        requester_email=requester_email,
        tenant_id=tenant_id
    )

    # Start background processing for all requests
    for req in requests:
        background_tasks.add_task(
            service.process_export_request,
            req.id
        )

    return {
        "message": f"Created {len(requests)} export requests",
        "request_ids": [req.id for req in requests]
    }


@router.get("/stats")
@limiter.limit("20/minute")
async def get_dsr_statistics(
    request,
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include in stats"),
    db: AsyncSession = Depends(get_db)
):
    """Get DSR request statistics."""
    service = DSRService(db)

    stats = await service.get_statistics(tenant_id=tenant_id, days=days)
    return stats
