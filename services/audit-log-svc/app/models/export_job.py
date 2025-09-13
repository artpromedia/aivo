"""Export job model for tracking audit log exports."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ExportStatus(str, Enum):
    """Export job status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ExportFormat(str, Enum):
    """Export format enumeration."""

    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"


class ExportJob(Base, TimestampMixin):
    """Export job tracking for audit log exports."""

    __tablename__ = "export_jobs"

    # Basic job information
    job_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable name for the export job"
    )

    requested_by: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User ID who requested the export"
    )

    status: Mapped[ExportStatus] = mapped_column(
        default=ExportStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Export parameters
    export_format: Mapped[ExportFormat] = mapped_column(
        nullable=False,
        comment="Format of the export (CSV, JSON, XLSX)"
    )

    # Filter criteria (stored as JSON for flexibility)
    filters: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Filter criteria applied to the export"
    )

    # Date range
    start_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Start date for export range"
    )

    end_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="End date for export range"
    )

    # Export results
    total_records: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Total number of records in export"
    )

    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Size of exported file in bytes"
    )

    # S3 storage information
    s3_bucket: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="S3 bucket where export is stored"
    )

    s3_key: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        comment="S3 key for the exported file"
    )

    download_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Signed URL for downloading the export"
    )

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When the export processing started"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="When the export completed"
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        index=True,
        comment="When the export download link expires"
    )

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if export failed"
    )

    # Additional metadata
    metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional export metadata"
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ExportJob(id={self.id}, name='{self.job_name}', "
            f"status='{self.status}', format='{self.export_format}')>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if the export has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_downloadable(self) -> bool:
        """Check if the export is ready for download."""
        return (
            self.status == ExportStatus.COMPLETED
            and self.download_url is not None
            and not self.is_expired
        )
