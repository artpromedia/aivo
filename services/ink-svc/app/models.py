"""
SQLAlchemy database models for ink capture service.

This module defines the database tables and relationships for storing
ink session metadata and tracking stroke submissions.
"""
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()


class InkSession(Base):
    """
    Database model for ink capture sessions.

    Tracks active drawing sessions with metadata for session management
    and analytics.
    """

    __tablename__ = "ink_sessions"

    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    learner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, index=True
    )
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self: Self) -> str:
        """String representation of the session."""
        return (
            f"<InkSession(session_id={self.session_id}, "
            f"learner_id={self.learner_id}, subject='{self.subject}', "
            f"status='{self.status}')>"
        )


class InkPage(Base):
    """
    Database model for ink pages within sessions.

    Tracks individual pages with their storage metadata and processing status.
    """

    __tablename__ = "ink_pages"

    page_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    learner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    s3_key: Mapped[str] = mapped_column(
        String(500), nullable=False, unique=True
    )
    canvas_width: Mapped[float] = mapped_column(Float, nullable=False)
    canvas_height: Mapped[float] = mapped_column(Float, nullable=False)
    stroke_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False
    )
    recognition_requested: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    recognition_job_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self: Self) -> str:
        """String representation of the page."""
        return (
            f"<InkPage(page_id={self.page_id}, "
            f"session_id={self.session_id}, "
            f"page_number={self.page_number}, "
            f"stroke_count={self.stroke_count})>"
        )


class StrokeMetrics(Base):
    """
    Database model for stroke analytics and metrics.

    Stores aggregated metrics for monitoring and analytics purposes.
    """

    __tablename__ = "stroke_metrics"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    learner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True
    )
    session_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stroke_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_drawing_time_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    avg_strokes_per_page: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    def __repr__(self: Self) -> str:
        """String representation of the metrics."""
        return (
            f"<StrokeMetrics(learner_id={self.learner_id}, "
            f"subject='{self.subject}', date={self.date.date()}, "
            f"stroke_count={self.stroke_count})>"
        )
