"""Test lesson service functionality."""

# ruff: noqa: ANN001
from uuid import UUID

import pytest

# pylint: disable=import-error,no-name-in-module
from app.lesson_service import LessonService
from app.models import AssetType, GradeBand, LessonState
from app.schemas import (
    AssetCreate,
    LessonCreate,
    LessonVersionCreate,
    SearchParams,
)


# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name,unused-argument
class TestLessonService:
    """Test lesson service operations."""

    @pytest.mark.asyncio
    async def test_create_lesson(self, db_session, test_user):
        """Test creating a lesson."""
        service = LessonService(db_session)

        lesson_data = LessonCreate(
            title="New Lesson",
            description="A new lesson for testing",
            subject="Science",
            grade_band=GradeBand.GRADES_3_5,
            keywords=["science", "test"],
        )

        lesson = await service.create_lesson(
            lesson_data, test_user.id, test_user.tenant_id
        )

        assert lesson.title == "New Lesson"
        assert lesson.subject == "Science"
        assert lesson.grade_band == GradeBand.GRADES_3_5
        assert lesson.created_by == test_user.id
        assert lesson.tenant_id == test_user.tenant_id

    @pytest.mark.asyncio
    async def test_get_lesson(self, db_session, test_lesson, test_user):
        """Test getting a lesson."""
        service = LessonService(db_session)

        lesson = await service.get_lesson(test_lesson.id, test_user.tenant_id)

        assert lesson is not None
        assert lesson.id == test_lesson.id
        assert lesson.title == test_lesson.title

    @pytest.mark.asyncio
    async def test_get_lesson_wrong_tenant(self, db_session, test_lesson):
        """Test getting a lesson with wrong tenant ID."""
        service = LessonService(db_session)

        wrong_tenant_id = UUID("99999999-9999-9999-9999-999999999999")
        lesson = await service.get_lesson(test_lesson.id, wrong_tenant_id)

        assert lesson is None

    @pytest.mark.asyncio
    async def test_create_version(self, db_session, test_lesson, test_user):
        """Test creating a lesson version."""
        service = LessonService(db_session)

        version_data = LessonVersionCreate(
            content={"slides": [{"title": "Test", "content": "Content"}]},
            summary="Test version",
            learning_objectives=["Learn something"],
            duration_minutes=45,
        )

        version = await service.create_version(
            test_lesson.id, version_data, test_user.tenant_id
        )

        assert version is not None
        assert version.lesson_id == test_lesson.id
        assert version.version_number == 1
        assert version.state == LessonState.DRAFT
        assert version.content == version_data.content

    @pytest.mark.asyncio
    async def test_publish_version(self, db_session, test_version, admin_user):
        """Test publishing a lesson version."""
        service = LessonService(db_session)

        published_version = await service.publish_version(
            test_version.id, admin_user.id, admin_user.tenant_id
        )

        assert published_version is not None
        assert published_version.state == LessonState.PUBLISHED
        assert published_version.published_by == admin_user.id
        assert published_version.published_at is not None

    @pytest.mark.asyncio
    async def test_add_asset(self, db_session, test_version, test_user):
        """Test adding an asset to a version."""
        service = LessonService(db_session)

        asset_data = AssetCreate(
            name="test-video.mp4",
            asset_type=AssetType.VIDEO,
            file_path="/videos/test-video.mp4",
            file_size=5120000,
            mime_type="video/mp4",
            alt_text="Test video",
        )

        asset = await service.add_asset(
            test_version.id, asset_data, test_user.tenant_id
        )

        assert asset is not None
        assert asset.name == "test-video.mp4"
        assert asset.asset_type == AssetType.VIDEO
        assert asset.version_id == test_version.id
        assert asset.s3_key is not None

    @pytest.mark.asyncio
    async def test_search_lessons(self, db_session, test_user):
        """Test searching lessons."""
        service = LessonService(db_session)

        # Create additional lessons for search
        lesson_data_2 = LessonCreate(
            title="Physics Lesson",
            description="Learn physics basics",
            subject="Physics",
            grade_band=GradeBand.GRADES_6_8,
            keywords=["physics", "science"],
        )

        await service.create_lesson(
            lesson_data_2, test_user.id, test_user.tenant_id
        )

        # Search by subject
        search_params = SearchParams(
            filters={"subject": "Mathematics"},
            page=1,
            page_size=10,
        )

        lessons, total = await service.search_lessons(
            search_params, test_user.tenant_id
        )

        assert total == 1
        assert len(lessons) == 1
        assert lessons[0].subject == "Mathematics"

        # Search by text query
        search_params = SearchParams(
            q="physics",
            page=1,
            page_size=10,
        )

        lessons, total = await service.search_lessons(
            search_params, test_user.tenant_id
        )

        assert total == 1
        assert len(lessons) == 1
        assert ("physics" in lessons[0].title.lower() or
                "physics" in lessons[0].keywords)

    @pytest.mark.asyncio
    async def test_delete_lesson(self, db_session, test_lesson, test_user):
        """Test deleting a lesson."""
        service = LessonService(db_session)

        success = await service.delete_lesson(
            test_lesson.id, test_user.tenant_id
        )
        assert success is True

        # Verify lesson is deleted
        lesson = await service.get_lesson(test_lesson.id, test_user.tenant_id)
        assert lesson is None
