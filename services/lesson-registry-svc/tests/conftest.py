"""Test configuration and fixtures."""
# pylint: disable=wrong-import-order

import asyncio
from collections.abc import AsyncGenerator, Generator
from uuid import UUID

import pytest

# pylint: disable=import-error,no-name-in-module
from app.auth import User
from app.database import Base, get_db
from app.main import app
from app.models import (
    AssetType,
    GradeBand,
    Lesson,
    LessonAsset,
    LessonVersion,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Test engine with in-memory database
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def override_get_db(
    db_session: AsyncSession,  # pylint: disable=redefined-outer-name
) -> Generator[None, None, None]:
    """Override get_db dependency."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    return User(
        id=UUID("12345678-1234-1234-1234-123456789abc"),
        tenant_id=UUID("87654321-4321-4321-4321-cba987654321"),
        email="test@example.com",
        roles=["teacher"],
    )


@pytest.fixture
def admin_user() -> User:
    """Create an admin user."""
    return User(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        tenant_id=UUID("87654321-4321-4321-4321-cba987654321"),
        email="admin@example.com",
        roles=["admin"],
    )


@pytest.fixture
async def test_lesson(
    db_session: AsyncSession,  # pylint: disable=redefined-outer-name
    test_user: User,  # pylint: disable=redefined-outer-name
) -> Lesson:
    """Create a test lesson."""
    lesson = Lesson(
        title="Test Lesson",
        description="A test lesson",
        subject="Mathematics",
        grade_band=GradeBand.K5,
        keywords=["math", "basic"],
        created_by=test_user.id,
        tenant_id=test_user.tenant_id,
    )

    db_session.add(lesson)
    await db_session.commit()
    await db_session.refresh(lesson)

    return lesson


@pytest.fixture
async def test_version(
    db_session: AsyncSession,  # pylint: disable=redefined-outer-name
    test_lesson: Lesson,  # pylint: disable=redefined-outer-name
) -> LessonVersion:
    """Create a test lesson version."""
    version = LessonVersion(
        lesson_id=test_lesson.id,
        version_number=1,
        content={"slides": [{"title": "Introduction", "content": "Welcome"}]},
        summary="Test version",
        learning_objectives=["Learn basics"],
        duration_minutes=30,
    )

    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)

    return version


@pytest.fixture
async def test_asset(
    db_session: AsyncSession,  # pylint: disable=redefined-outer-name
    test_version: LessonVersion,  # pylint: disable=redefined-outer-name
) -> LessonAsset:
    """Create a test asset."""
    asset = LessonAsset(
        version_id=test_version.id,
        name="test-image.png",
        asset_type=AssetType.IMAGE,
        file_path="/images/test-image.png",
        file_size=1024,
        mime_type="image/png",
        s3_bucket="test-bucket",
        s3_key="lessons/test/assets/test-image.png",
    )

    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)

    return asset
