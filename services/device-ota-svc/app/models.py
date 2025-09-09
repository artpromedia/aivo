"""Database models for Device OTA & Heartbeat Service."""
# flake8: noqa: E501

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Base class for all database models."""


class UpdateType(str, Enum):  # pylint: disable=too-few-public-methods
    """Type of update being deployed."""

    FIRMWARE = "firmware"
    APPLICATION = "application"
    CONFIGURATION = "configuration"


class DeploymentRing(str, Enum):  # pylint: disable=too-few-public-methods
    """Deployment ring for staged rollouts."""

    CANARY = "canary"
    EARLY = "early"
    BROAD = "broad"
    PRODUCTION = "production"


class UpdateStatus(str, Enum):  # pylint: disable=too-few-public-methods
    """Status of update deployment."""

    CREATED = "created"
    TESTING = "testing"
    DEPLOYED = "deployed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class DeviceUpdateStatus(str, Enum):  # pylint: disable=too-few-public-methods
    """Status of update on individual device."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class FirmwareUpdate(Base):  # pylint: disable=too-few-public-methods
    """Firmware/application update releases."""

    __tablename__ = "firmware_updates"

    update_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    update_type: Mapped[UpdateType] = mapped_column(
        String(20), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    previous_version: Mapped[str] = mapped_column(String(50), nullable=True)

    # Update metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    release_notes: Mapped[str] = mapped_column(Text, nullable=True)
    changelog: Mapped[list[dict]] = mapped_column(JSON, nullable=True)

    # Deployment configuration
    deployment_ring: Mapped[DeploymentRing] = mapped_column(
        String(20), default=DeploymentRing.CANARY, index=True
    )
    status: Mapped[UpdateStatus] = mapped_column(
        String(20), default=UpdateStatus.CREATED, index=True
    )
    target_device_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    minimum_battery_level: Mapped[int] = mapped_column(Integer, default=50)

    # File information
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    signature: Mapped[str] = mapped_column(String(512), nullable=True)
    download_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Rollout configuration
    canary_percentage: Mapped[float] = mapped_column(Float, default=5.0)
    early_percentage: Mapped[float] = mapped_column(Float, default=25.0)
    broad_percentage: Mapped[float] = mapped_column(Float, default=75.0)
    auto_rollback_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_threshold_percentage: Mapped[float] = mapped_column(Float, default=10.0)

    # Scheduling
    scheduled_deployment: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    deployment_window_hours: Mapped[int] = mapped_column(Integer, default=6)
    force_update: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )
    deployed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Rollback information
    rollback_reason: Mapped[str] = mapped_column(Text, nullable=True)
    rollback_initiated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    rollback_completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Created by
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Relationships
    device_updates: Mapped[list["DeviceUpdate"]] = relationship(
        "DeviceUpdate", back_populates="firmware_update", lazy="select"
    )


class DeviceUpdate(Base):  # pylint: disable=too-few-public-methods
    """Track update deployment to individual devices."""

    __tablename__ = "device_updates"

    device_update_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    update_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("firmware_updates.update_id"),
        nullable=False,
        index=True
    )
    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )

    # Update status
    status: Mapped[DeviceUpdateStatus] = mapped_column(
        String(20), default=DeviceUpdateStatus.PENDING, index=True
    )
    assigned_ring: Mapped[DeploymentRing] = mapped_column(
        String(20), nullable=False, index=True
    )

    # Progress tracking
    download_progress: Mapped[float] = mapped_column(Float, default=0.0)
    install_progress: Mapped[float] = mapped_column(Float, default=0.0)

    # Device state at update time
    current_version: Mapped[str] = mapped_column(String(50), nullable=True)
    target_version: Mapped[str] = mapped_column(String(50), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    battery_level: Mapped[int] = mapped_column(Integer, nullable=True)
    storage_available_mb: Mapped[int] = mapped_column(Integer, nullable=True)

    # Timing
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Error handling
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    # Rollback tracking
    rollback_version: Mapped[str] = mapped_column(String(50), nullable=True)
    rolled_back_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    firmware_update: Mapped["FirmwareUpdate"] = relationship(
        "FirmwareUpdate", back_populates="device_updates", lazy="select"
    )


class DeviceHeartbeat(Base):  # pylint: disable=too-few-public-methods
    """Device heartbeat and telemetry data."""

    __tablename__ = "device_heartbeats"

    heartbeat_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )

    # Device identification
    device_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    hardware_model: Mapped[str] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    # Software versions
    firmware_version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    application_version: Mapped[str] = mapped_column(String(50), nullable=True)
    bootloader_version: Mapped[str] = mapped_column(String(50), nullable=True)

    # System status
    uptime_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    battery_level: Mapped[int] = mapped_column(Integer, nullable=True)
    charging_status: Mapped[bool] = mapped_column(Boolean, nullable=True)
    cpu_usage_percent: Mapped[float] = mapped_column(Float, nullable=True)
    memory_usage_percent: Mapped[float] = mapped_column(Float, nullable=True)
    storage_used_mb: Mapped[int] = mapped_column(Integer, nullable=True)
    storage_total_mb: Mapped[int] = mapped_column(Integer, nullable=True)

    # Network status
    network_type: Mapped[str] = mapped_column(String(20), nullable=True)  # wifi, cellular, ethernet
    signal_strength: Mapped[int] = mapped_column(Integer, nullable=True)  # RSSI or bars
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    last_connectivity_test: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Location (if available)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    location_accuracy: Mapped[float] = mapped_column(Float, nullable=True)

    # Update status
    pending_update_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    last_update_check: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    update_available: Mapped[bool] = mapped_column(Boolean, default=False)

    # Error reporting
    recent_errors: Mapped[list[dict]] = mapped_column(JSON, nullable=True)
    crash_count_24h: Mapped[int] = mapped_column(Integer, default=0)
    last_crash_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Custom telemetry
    custom_metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Timing
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )


class UpdateRolloutMetrics(Base):  # pylint: disable=too-few-public-methods
    """Aggregated metrics for update rollouts."""

    __tablename__ = "update_rollout_metrics"

    metric_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    update_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )
    deployment_ring: Mapped[DeploymentRing] = mapped_column(
        String(20), nullable=False, index=True
    )

    # Rollout statistics
    total_devices: Mapped[int] = mapped_column(Integer, default=0)
    pending_devices: Mapped[int] = mapped_column(Integer, default=0)
    downloading_devices: Mapped[int] = mapped_column(Integer, default=0)
    installing_devices: Mapped[int] = mapped_column(Integer, default=0)
    completed_devices: Mapped[int] = mapped_column(Integer, default=0)
    failed_devices: Mapped[int] = mapped_column(Integer, default=0)

    # Success rates
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    failure_rate: Mapped[float] = mapped_column(Float, default=0.0)
    rollback_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Performance metrics
    average_download_time_minutes: Mapped[float] = mapped_column(Float, nullable=True)
    average_install_time_minutes: Mapped[float] = mapped_column(Float, nullable=True)
    bandwidth_usage_mb: Mapped[float] = mapped_column(Float, nullable=True)

    # Health indicators
    crash_rate_increase: Mapped[float] = mapped_column(Float, default=0.0)
    battery_drain_increase: Mapped[float] = mapped_column(Float, default=0.0)
    performance_regression: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), index=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
