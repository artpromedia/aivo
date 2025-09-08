"""API routes for lesson registry."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import (
    User,
    can_edit_lesson,
    can_publish_lesson,
    get_current_user,
    require_admin,
    require_teacher,
)
from .cdn_service import cdn_service
from .database import get_db
from .lesson_service import get_lesson_service
from .schemas import (
    Asset,
    AssetCreate,
    Lesson,
    LessonCreate,
    LessonUpdate,
    LessonVersion,
    LessonVersionCreate,
    LessonVersionUpdate,
    PublishResponse,
    SearchParams,
    SearchResults,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["lessons"])


@router.post("/lessons", response_model=Lesson, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson_data: LessonCreate,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    """Create a new lesson."""
    lesson_service = get_lesson_service(db)
    lesson = await lesson_service.create_lesson(
        lesson_data, current_user.id, current_user.tenant_id
    )
    return lesson


@router.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    """Get a lesson by ID."""
    lesson_service = get_lesson_service(db)
    lesson = await lesson_service.get_lesson(lesson_id, current_user.tenant_id)

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    return lesson


@router.put("/lessons/{lesson_id}", response_model=Lesson)
async def update_lesson(
    lesson_id: UUID,
    lesson_data: LessonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Lesson:
    """Update a lesson."""
    lesson_service = get_lesson_service(db)

    # Check if lesson exists
    existing_lesson = await lesson_service.get_lesson(lesson_id, current_user.tenant_id)
    if not existing_lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    # Check permissions
    if not can_edit_lesson(current_user, existing_lesson.created_by, existing_lesson.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to edit this lesson",
        )

    lesson = await lesson_service.update_lesson(lesson_id, lesson_data, current_user.tenant_id)
    return lesson


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a lesson."""
    lesson_service = get_lesson_service(db)

    # Check if lesson exists
    existing_lesson = await lesson_service.get_lesson(lesson_id, current_user.tenant_id)
    if not existing_lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    # Check permissions
    if not can_edit_lesson(current_user, existing_lesson.created_by, existing_lesson.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete this lesson",
        )

    success = await lesson_service.delete_lesson(lesson_id, current_user.tenant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")


@router.post(
    "/lessons/{lesson_id}/versions",
    response_model=LessonVersion,
    status_code=status.HTTP_201_CREATED,
)
async def create_lesson_version(
    lesson_id: UUID,
    version_data: LessonVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonVersion:
    """Create a new version of a lesson."""
    lesson_service = get_lesson_service(db)

    # Check if lesson exists and user can edit it
    existing_lesson = await lesson_service.get_lesson(lesson_id, current_user.tenant_id)
    if not existing_lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    if not can_edit_lesson(current_user, existing_lesson.created_by, existing_lesson.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create version for this lesson",
        )

    version = await lesson_service.create_version(lesson_id, version_data, current_user.tenant_id)
    return version


@router.put("/versions/{version_id}", response_model=LessonVersion)
async def update_lesson_version(
    version_id: UUID,
    version_data: LessonVersionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonVersion:
    """Update a lesson version (only if in DRAFT state)."""
    lesson_service = get_lesson_service(db)
    version = await lesson_service.update_version(version_id, version_data, current_user.tenant_id)

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found or not in draft state"
        )

    return version


@router.post("/versions/{version_id}/publish", response_model=PublishResponse)
async def publish_lesson_version(
    version_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PublishResponse:
    """Publish a lesson version (admin only)."""
    lesson_service = get_lesson_service(db)

    # Check if user can publish (admin only)
    if not can_publish_lesson(current_user, current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to publish lessons",
        )

    version = await lesson_service.publish_version(
        version_id, current_user.id, current_user.tenant_id
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found or not in draft state"
        )

    return PublishResponse(
        success=True, message="Lesson version published successfully", version=version
    )


@router.post(
    "/versions/{version_id}/assets", response_model=Asset, status_code=status.HTTP_201_CREATED
)
async def add_asset_to_version(
    version_id: UUID,
    asset_data: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Asset:
    """Add an asset to a lesson version."""
    lesson_service = get_lesson_service(db)
    asset = await lesson_service.add_asset(version_id, asset_data, current_user.tenant_id)

    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    return asset


@router.get("/assets/{asset_id}/upload-url")
async def get_asset_upload_url(
    asset_id: UUID,
    content_type: str = Query(..., description="Content type of the asset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a presigned URL for uploading an asset."""
    # pylint: disable=fixme,unused-argument
    # TODO: Implement asset lookup and permission check
    # For now, generate a generic upload URL

    # Generate S3 key based on asset ID
    s3_key = f"temp/{asset_id}"

    upload_data = await cdn_service.generate_upload_url(s3_key, content_type)

    if not upload_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL",
        )

    return upload_data


@router.get("/search", response_model=SearchResults)
async def search_lessons(
    q: str = Query(None, description="Search query"),
    subject: str = Query(None, description="Filter by subject"),
    grade_band: str = Query(None, description="Filter by grade band"),
    keywords: list[str] = Query(default=[], description="Filter by keywords"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResults:
    """Search lessons with filters and pagination."""
    lesson_service = get_lesson_service(db)

    # Build search parameters
    search_params = SearchParams(
        q=q,
        filters={
            "subject": subject,
            "grade_band": grade_band,
            "keywords": keywords,
        },
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    lessons, total = await lesson_service.search_lessons(search_params, current_user.tenant_id)

    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1

    return SearchResults(
        lessons=lessons,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
    )
