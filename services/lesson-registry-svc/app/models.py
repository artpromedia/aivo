"""Database models for lesson registry service."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()


class LessonState(str, Enum):
    """Lesson states."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class AssetType(str, Enum):
    """Asset types."""

    VIDEO = "video"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    INTERACTIVE = "interactive"


class GradeBand(str, Enum):
    """Grade bands."""

    K2 = "K-2"
    K5 = "K-5"
    GRADES_3_5 = "3-5"
    GRADES_6_8 = "6-8"
    GRADES_9_12 = "9-12"
    ADULT = "adult"


class Lesson(Base):
    """Lesson model."""

    __tablename__ = "lessons"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    grade_band: Mapped[GradeBand] = mapped_column(SQLEnum(GradeBand), nullable=False, index=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSONB)
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # Ownership and permissions
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    versions: Mapped[list["LessonVersion"]] = relationship(
        "LessonVersion", back_populates="lesson", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Lesson(id={self.id}, title='{self.title}', subject='{self.subject}')>"


class LessonVersion(Base):
    """Lesson version model."""

    __tablename__ = "lesson_versions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    lesson_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[LessonState] = mapped_column(
        SQLEnum(LessonState), nullable=False, default=LessonState.DRAFT
    )

    # Content
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    learning_objectives: Mapped[list[str] | None] = mapped_column(JSONB)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    # Publishing info
    published_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="versions")
    assets: Mapped[list["LessonAsset"]] = relationship(
        "LessonAsset", back_populates="version", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<LessonVersion(id={self.id}, lesson_id={self.lesson_id}, "
            f"version={self.version_number}, state={self.state})>"
        )


class LessonAsset(Base):
    """Lesson asset model."""

    __tablename__ = "lesson_assets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("lesson_versions.id"), nullable=False
    )

    # Asset info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(SQLEnum(AssetType), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # CDN info
    cdn_url: Mapped[str | None] = mapped_column(String(500))
    s3_bucket: Mapped[str | None] = mapped_column(String(100))
    s3_key: Mapped[str | None] = mapped_column(String(500))

    # Metadata
    extra_metadata: Mapped[dict | None] = mapped_column(JSONB)
    alt_text: Mapped[str | None] = mapped_column(String(500))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationships
    version: Mapped["LessonVersion"] = relationship("LessonVersion", back_populates="assets")

    def __repr__(self) -> str:
        return f"<LessonAsset(id={self.id}, name='{self.name}', type={self.asset_type})>"
