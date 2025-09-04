"""Lesson service with business logic."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import count
from sqlalchemy.sql.functions import max as sql_max

from .cdn_service import cdn_service
from .models import Lesson, LessonAsset, LessonState, LessonVersion
from .schemas import (
    AssetCreate,
    LessonCreate,
    LessonUpdate,
    LessonVersionCreate,
    LessonVersionUpdate,
    SearchParams,
)

logger = logging.getLogger(__name__)


class LessonService:
    """Service for lesson operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_lesson(
        self,
        lesson_data: LessonCreate,
        created_by: UUID,
        tenant_id: UUID
    ) -> Lesson:
        """Create a new lesson."""
        lesson = Lesson(
            title=lesson_data.title,
            description=lesson_data.description,
            subject=lesson_data.subject,
            grade_band=lesson_data.grade_band,
            keywords=lesson_data.keywords,
            extra_metadata=lesson_data.extra_metadata,
            created_by=created_by,
            tenant_id=tenant_id,
        )

        self.db.add(lesson)
        await self.db.commit()
        await self.db.refresh(lesson)

        logger.info("Created lesson %s by user %s", lesson.id, created_by)
        return lesson

    async def get_lesson(
        self, lesson_id: UUID, tenant_id: UUID
    ) -> Lesson | None:
        """Get a lesson by ID."""
        stmt = (
            select(Lesson)
            .options(
                selectinload(Lesson.versions).selectinload(
                    LessonVersion.assets
                )
            )
            .where(and_(Lesson.id == lesson_id, Lesson.tenant_id == tenant_id))
        )

        result = await self.db.execute(stmt)
        lesson = result.scalar_one_or_none()

        if lesson:
            # Add presigned URLs to assets
            await self._add_asset_urls(lesson)

        return lesson

    async def update_lesson(
        self,
        lesson_id: UUID,
        lesson_data: LessonUpdate,
        tenant_id: UUID
    ) -> Lesson | None:
        """Update a lesson."""
        stmt = select(Lesson).where(
            and_(Lesson.id == lesson_id, Lesson.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        lesson = result.scalar_one_or_none()

        if not lesson:
            return None

        # Update fields
        for field, value in lesson_data.model_dump(exclude_unset=True).items():
            setattr(lesson, field, value)

        await self.db.commit()
        await self.db.refresh(lesson)

        logger.info("Updated lesson %s", lesson_id)
        return lesson

    async def delete_lesson(self, lesson_id: UUID, tenant_id: UUID) -> bool:
        """Delete a lesson and all its versions."""
        stmt = select(Lesson).where(
            and_(Lesson.id == lesson_id, Lesson.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        lesson = result.scalar_one_or_none()

        if not lesson:
            return False

        # Delete associated S3 objects
        await self._cleanup_lesson_assets(lesson_id)

        await self.db.delete(lesson)
        await self.db.commit()

        logger.info("Deleted lesson %s", lesson_id)
        return True

    async def create_version(
        self,
        lesson_id: UUID,
        version_data: LessonVersionCreate,
        tenant_id: UUID
    ) -> LessonVersion | None:
        """Create a new version of a lesson."""
        # Check if lesson exists and belongs to tenant
        lesson = await self.get_lesson(lesson_id, tenant_id)
        if not lesson:
            return None

        # Get next version number
        stmt = (
            select(sql_max(LessonVersion.version_number))
            .where(LessonVersion.lesson_id == lesson_id)
        )
        result = await self.db.execute(stmt)
        max_version = result.scalar() or 0

        version = LessonVersion(
            lesson_id=lesson_id,
            version_number=max_version + 1,
            content=version_data.content,
            summary=version_data.summary,
            learning_objectives=version_data.learning_objectives,
            duration_minutes=version_data.duration_minutes,
        )

        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)

        logger.info(
            "Created version %s for lesson %s",
            version.version_number, lesson_id
        )
        return version

    async def update_version(
        self,
        version_id: UUID,
        version_data: LessonVersionUpdate,
        tenant_id: UUID
    ) -> LessonVersion | None:
        """Update a lesson version."""
        stmt = (
            select(LessonVersion)
            .join(Lesson)
            .where(
                and_(
                    LessonVersion.id == version_id,
                    Lesson.tenant_id == tenant_id,
                    LessonVersion.state == LessonState.DRAFT
                )
            )
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()

        if not version:
            return None

        # Update fields
        update_data = version_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(version, field, value)

        await self.db.commit()
        await self.db.refresh(version)

        logger.info("Updated version %s", version_id)
        return version

    async def publish_version(
        self,
        version_id: UUID,
        published_by: UUID,
        tenant_id: UUID
    ) -> LessonVersion | None:
        """Publish a lesson version."""
        stmt = (
            select(LessonVersion)
            .join(Lesson)
            .where(
                and_(
                    LessonVersion.id == version_id,
                    Lesson.tenant_id == tenant_id,
                    LessonVersion.state == LessonState.DRAFT
                )
            )
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()

        if not version:
            return None

        # Update version state
        version.state = LessonState.PUBLISHED
        version.published_by = published_by
        version.published_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(version)

        logger.info(
            "Published version %s by user %s", version_id, published_by
        )
        return version

    async def add_asset(
        self,
        version_id: UUID,
        asset_data: AssetCreate,
        tenant_id: UUID
    ) -> LessonAsset | None:
        """Add an asset to a lesson version."""
        # Check if version exists and belongs to tenant
        stmt = (
            select(LessonVersion)
            .join(Lesson)
            .where(
                and_(
                    LessonVersion.id == version_id,
                    Lesson.tenant_id == tenant_id
                )
            )
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()

        if not version:
            return None

        # Generate S3 key
        s3_key = cdn_service.generate_asset_key(
            version.lesson_id, version_id, asset_data.name
        )

        asset = LessonAsset(
            version_id=version_id,
            name=asset_data.name,
            asset_type=asset_data.asset_type,
            file_path=asset_data.file_path,
            file_size=asset_data.file_size,
            mime_type=asset_data.mime_type,
            alt_text=asset_data.alt_text,
            extra_metadata=asset_data.extra_metadata,
            s3_bucket=cdn_service.bucket_name,
            s3_key=s3_key,
        )

        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)

        logger.info("Added asset %s to version %s", asset.id, version_id)
        return asset

    async def search_lessons(
        self,
        search_params: SearchParams,
        tenant_id: UUID
    ) -> tuple[list[Lesson], int]:
        """Search lessons with filters and pagination."""
        # Base query
        stmt = select(Lesson).where(Lesson.tenant_id == tenant_id)

        # Apply search query
        if search_params.q:
            search_term = f"%{search_params.q}%"
            stmt = stmt.where(
                or_(
                    Lesson.title.ilike(search_term),
                    Lesson.description.ilike(search_term),
                    Lesson.keywords.op("@>")(f'["{search_params.q}"]')
                )
            )

        # Apply filters
        if search_params.filters:
            if search_params.filters.subject:
                stmt = stmt.where(
                    Lesson.subject == search_params.filters.subject
                )

            if search_params.filters.grade_band:
                stmt = stmt.where(
                    Lesson.grade_band == search_params.filters.grade_band
                )

            if search_params.filters.keywords:
                for keyword in search_params.filters.keywords:
                    stmt = stmt.where(
                        Lesson.keywords.op("@>")(f'["{keyword}"]')
                    )

            if search_params.filters.created_by:
                stmt = stmt.where(
                    Lesson.created_by == search_params.filters.created_by
                )

        # Get total count by counting rows from the base query
        count_result = await self.db.execute(
            select(count()).select_from(
                stmt.subquery()
            )
        )
        total = count_result.scalar()

        # Apply sorting
        if search_params.sort_by == "title":
            order_col = Lesson.title
        elif search_params.sort_by == "subject":
            order_col = Lesson.subject
        elif search_params.sort_by == "updated_at":
            order_col = Lesson.updated_at
        else:
            order_col = Lesson.created_at

        if search_params.sort_order == "desc":
            order_col = desc(order_col)

        stmt = stmt.order_by(order_col)

        # Apply pagination
        offset = (search_params.page - 1) * search_params.page_size
        stmt = stmt.offset(offset).limit(search_params.page_size)

        # Load with relationships
        stmt = stmt.options(
            selectinload(Lesson.versions).selectinload(LessonVersion.assets)
        )

        result = await self.db.execute(stmt)
        lessons = result.scalars().all()

        # Add presigned URLs to assets
        for lesson in lessons:
            await self._add_asset_urls(lesson)

        return list(lessons), total

    async def _add_asset_urls(self, lesson: Lesson) -> None:
        """Add presigned URLs to lesson assets."""
        for version in lesson.versions:
            for asset in version.assets:
                if asset.s3_key:
                    signed_url = await cdn_service.generate_presigned_url(
                        asset.s3_key
                    )
                    asset.signed_url = signed_url

    async def _cleanup_lesson_assets(self, lesson_id: UUID) -> None:
        """Clean up S3 assets for a lesson."""
        # Get all versions and their assets
        stmt = (
            select(LessonAsset)
            .join(LessonVersion)
            .where(LessonVersion.lesson_id == lesson_id)
        )
        result = await self.db.execute(stmt)
        assets = result.scalars().all()

        # Delete S3 objects
        for asset in assets:
            if asset.s3_key:
                await cdn_service.delete_object(asset.s3_key)

        logger.info(
            "Cleaned up %s assets for lesson %s", len(assets), lesson_id
        )


def get_lesson_service(db: AsyncSession) -> LessonService:
    """Get lesson service instance."""
    return LessonService(db)
