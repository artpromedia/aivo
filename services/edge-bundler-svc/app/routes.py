"""FastAPI routes for Edge Bundler Service."""
# flake8: noqa: E501

import os
from datetime import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import BundleStatus
from app.schemas import (
    BundleListResponse,
    BundleRequest,
    BundleResponse,
    BundleStatsResponse,
    CRDTMergeRequest,
    CRDTMergeResponse,
    DownloadRequest,
    DownloadResponse,
    HealthResponse,
)
from app.services import BundleService, CRDTService, DownloadService

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()

# Initialize services
bundle_service = BundleService()
crdt_service = CRDTService()
download_service = DownloadService()


# Bundle creation and management endpoints
@router.post(
    "/bundles",
    response_model=BundleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create offline lesson bundle",
    description="Create a new signed offline bundle with ≤50MB pre-cache and CRDT merge hooks",
)
async def create_bundle(
    bundle_request: BundleRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BundleResponse:
    """Create a new offline lesson bundle."""
    try:
        # Validate size constraints
        if bundle_request.max_bundle_size > 52428800:  # 50MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bundle size cannot exceed 50MB limit",
            )

        if bundle_request.max_precache_size > 26214400:  # 25MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Precache size cannot exceed 25MB limit",
            )

        # Get user from request headers (in production, use proper auth)
        created_by = request.headers.get("X-User-ID")

        bundle = await bundle_service.create_bundle(bundle_request, db, _created_by=created_by)

        logger.info(
            "Bundle creation initiated",
            bundle_id=bundle.bundle_id,
            learner_id=bundle_request.learner_id,
            subjects=bundle_request.subjects,
            max_size=bundle_request.max_bundle_size,
        )

        return BundleResponse.from_orm(bundle)

    except ValueError as e:
        logger.warning("Invalid bundle request", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to create bundle", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create bundle"
        ) from e


@router.get("/bundles/{bundle_id}", response_model=BundleResponse)
async def get_bundle(
    bundle_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BundleResponse:
    """Get bundle details by ID."""
    bundle = await bundle_service.get_bundle(bundle_id, db)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")
    return BundleResponse.from_orm(bundle)


@router.get("/bundles", response_model=BundleListResponse)
async def list_bundles(
    learner_id: Annotated[UUID | None, Query()] = None,
    status_filter: Annotated[BundleStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> BundleListResponse:
    """List bundles with optional filtering."""
    offset = (page - 1) * size
    bundles, total = await bundle_service.list_bundles(
        learner_id=learner_id,
        status=status_filter,
        limit=size,
        offset=offset,
        db=db,
    )

    pages = (total + size - 1) // size

    return BundleListResponse(
        bundles=[BundleResponse.from_orm(b) for b in bundles],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.delete("/bundles/{bundle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bundle(
    bundle_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a bundle and its files."""
    bundle = await bundle_service.get_bundle(bundle_id, db)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")

    # TODO: Implement bundle deletion with file cleanup  # pylint: disable=fixme
    logger.info("Bundle deletion requested", bundle_id=bundle_id)


# Bundle download endpoints
@router.post("/bundles/{bundle_id}/download", response_model=DownloadResponse)
async def initiate_download(
    bundle_id: UUID,
    download_request: DownloadRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DownloadResponse:
    """Initiate bundle download."""
    bundle = await bundle_service.get_bundle(bundle_id, db)
    if not bundle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")

    if bundle.status != BundleStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bundle is not ready for download (status: {bundle.status})",
        )

    # Create download record
    download = await download_service.create_download(
        bundle_id=bundle_id,
        learner_id=download_request.learner_id,
        user_agent=request.headers.get("User-Agent"),
        client_ip=request.client.host,
        client_version=download_request.client_version,
        db=db,
    )

    # Generate download URLs (in production, use signed URLs)
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    download_url = f"{base_url}/api/v1/bundles/{bundle_id}/files/bundle"
    manifest_url = (
        f"{base_url}/api/v1/bundles/{bundle_id}/files/manifest"
        if download_request.include_manifest
        else None
    )

    return DownloadResponse(
        bundle_id=bundle_id,
        download_url=download_url,
        manifest_url=manifest_url,
        size=bundle.actual_size or 0,
        sha256_hash=bundle.sha256_hash or "",
        expires_at=bundle.expires_at or datetime.utcnow(),
        download_id=download.download_id,
    )


@router.get("/bundles/{bundle_id}/files/bundle")
async def download_bundle_file(
    bundle_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    """Download the actual bundle file."""
    bundle = await bundle_service.get_bundle(bundle_id, db)
    if not bundle or not bundle.bundle_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle file not found")

    if not os.path.exists(bundle.bundle_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bundle file not found on disk"
        )

    return FileResponse(
        path=bundle.bundle_path,
        filename=f"{bundle.bundle_name}.tar.gz",
        media_type="application/gzip",
    )


@router.get("/bundles/{bundle_id}/files/manifest")
async def download_manifest_file(
    bundle_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    """Download the bundle manifest file."""
    bundle = await bundle_service.get_bundle(bundle_id, db)
    if not bundle or not bundle.manifest_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manifest file not found")

    if not os.path.exists(bundle.manifest_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Manifest file not found on disk"
        )

    return FileResponse(
        path=bundle.manifest_path,
        filename=f"{bundle.bundle_name}_manifest.json",
        media_type="application/json",
    )


# CRDT synchronization endpoints
@router.post("/bundles/{bundle_id}/crdt/merge", response_model=CRDTMergeResponse)
async def merge_crdt_operations(
    bundle_id: UUID,
    merge_request: CRDTMergeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CRDTMergeResponse:
    """Merge CRDT operations from offline client."""
    try:
        # Validate bundle exists
        bundle = await bundle_service.get_bundle(bundle_id, db)
        if not bundle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")

        # Ensure bundle ID matches request
        merge_request.bundle_id = bundle_id

        result = await crdt_service.merge_operations(merge_request, db)

        logger.info(
            "CRDT merge completed",
            bundle_id=bundle_id,
            learner_id=merge_request.learner_id,
            accepted=len(result.accepted_operations),
            conflicted=len(result.conflicted_operations),
        )

        return result

    except Exception as e:
        logger.error("CRDT merge failed", bundle_id=bundle_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to merge CRDT operations",
        ) from e


# Statistics and monitoring endpoints
@router.get("/bundles/stats", response_model=BundleStatsResponse)
async def get_bundle_statistics() -> BundleStatsResponse:
    """Get bundle creation and download statistics."""
    # TODO: Implement comprehensive statistics  # pylint: disable=fixme
    return BundleStatsResponse(
        total_bundles=0,
        active_bundles=0,
        total_size_bytes=0,
        average_size_bytes=0,
        download_count=0,
        most_popular_subjects=[],
        crdt_operations_count=0,
        conflict_resolution_count=0,
    )


# Health check endpoint
@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    try:
        # Check storage path availability
        storage_path = os.getenv("BUNDLE_STORAGE_PATH", "/tmp/bundles")
        storage_available = os.path.exists(storage_path) and os.access(storage_path, os.W_OK)

        dependencies = {
            "database": "healthy",  # TODO: Add actual DB health check  # pylint: disable=fixme
            "storage": "healthy" if storage_available else "unhealthy",
        }

        return HealthResponse(
            status=(
                "healthy" if all(dep == "healthy" for dep in dependencies.values()) else "degraded"
            ),
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies=dependencies,
            metrics={
                "storage_available": storage_available,
            },
        )

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        ) from e
