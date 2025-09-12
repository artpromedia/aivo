"""Pydantic schemas for Device OTA & Heartbeat Service."""
# flake8: noqa: E501

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models import (
    DeploymentRing,
    DeviceUpdateStatus,
    UpdateStatus,
    UpdateType,
)


class FirmwareUpdateRequest(BaseModel):
    """Schema for creating a new firmware update."""

    update_type: UpdateType = Field(..., description="Type of update")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+", description="Semantic version")
    previous_version: str | None = Field(None, description="Version being updated from")
    title: str = Field(..., max_length=255, description="Update title")
    description: str | None = Field(None, description="Update description")
    release_notes: str | None = Field(None, description="Release notes")
    changelog: list[dict] | None = Field(None, description="Structured changelog")

    # Deployment configuration
    target_device_types: list[str] = Field(..., min_items=1, description="Target device types")
    minimum_battery_level: int = Field(
        50, ge=10, le=100, description="Minimum battery level required"
    )

    # File information
    file_path: str = Field(..., description="Path to update file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    checksum: str = Field(..., description="SHA256 checksum")
    signature: str | None = Field(None, description="Digital signature")

    # Rollout configuration
    canary_percentage: float = Field(5.0, ge=0.1, le=50.0, description="Canary rollout percentage")
    early_percentage: float = Field(25.0, ge=5.0, le=75.0, description="Early adopter percentage")
    broad_percentage: float = Field(
        75.0, ge=25.0, le=95.0, description="Broad deployment percentage"
    )
    auto_rollback_enabled: bool = Field(True, description="Enable automatic rollback")
    failure_threshold_percentage: float = Field(
        10.0, ge=1.0, le=50.0, description="Failure rate threshold for rollback"
    )

    # Scheduling
    scheduled_deployment: datetime | None = Field(None, description="Scheduled deployment time")
    deployment_window_hours: int = Field(6, ge=1, le=24, description="Deployment window duration")
    force_update: bool = Field(False, description="Force update on all devices")

    @validator("early_percentage")
    @classmethod
    def validate_early_percentage(
        cls: type["FirmwareUpdateRequest"], v: float, values: dict
    ) -> float:
        """Ensure early percentage is greater than canary percentage."""
        if "canary_percentage" in values and v <= values["canary_percentage"]:
            raise ValueError("Early percentage must be greater than canary percentage")
        return v

    @validator("broad_percentage")
    @classmethod
    def validate_broad_percentage(
        cls: type["FirmwareUpdateRequest"], v: float, values: dict
    ) -> float:
        """Ensure broad percentage is greater than early percentage."""
        if "early_percentage" in values and v <= values["early_percentage"]:
            raise ValueError("Broad percentage must be greater than early percentage")
        return v


class FirmwareUpdateResponse(BaseModel):
    """Schema for firmware update response."""

    update_id: UUID
    update_type: UpdateType
    version: str
    previous_version: str | None
    title: str
    description: str | None
    status: UpdateStatus
    deployment_ring: DeploymentRing
    target_device_types: list[str]

    # File information
    file_size: int
    checksum: str
    download_url: str | None

    # Rollout configuration
    canary_percentage: float
    early_percentage: float
    broad_percentage: float
    auto_rollback_enabled: bool
    failure_threshold_percentage: float

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deployed_at: datetime | None
    completed_at: datetime | None
    scheduled_deployment: datetime | None

    # Rollback information
    rollback_reason: str | None
    rollback_initiated_at: datetime | None

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic configuration."""

        from_attributes = True


class UpdateCheckRequest(BaseModel):
    """Schema for device update check."""

    device_id: UUID = Field(..., description="Device identifier")
    device_type: str = Field(..., description="Device type")
    current_firmware_version: str = Field(..., description="Current firmware version")
    current_app_version: str | None = Field(None, description="Current app version")
    hardware_model: str | None = Field(None, description="Hardware model")
    battery_level: int | None = Field(None, ge=0, le=100, description="Battery level")
    storage_available_mb: int | None = Field(None, ge=0, description="Available storage MB")
    network_type: str | None = Field(None, description="Network connection type")


class UpdateCheckResponse(BaseModel):
    """Schema for update check response."""

    update_available: bool = Field(..., description="Whether update is available")
    update_id: UUID | None = Field(None, description="Update identifier if available")
    update_type: UpdateType | None = Field(None, description="Type of available update")
    target_version: str | None = Field(None, description="Target version")
    title: str | None = Field(None, description="Update title")
    description: str | None = Field(None, description="Update description")
    release_notes: str | None = Field(None, description="Release notes")

    # Download information
    download_url: str | None = Field(None, description="Download URL")
    file_size: int | None = Field(None, description="File size in bytes")
    checksum: str | None = Field(None, description="File checksum")

    # Update requirements
    minimum_battery_level: int | None = Field(None, description="Required battery level")
    required_storage_mb: int | None = Field(None, description="Required storage space")
    force_update: bool = Field(False, description="Whether update is mandatory")

    # Scheduling
    deployment_window_start: datetime | None = Field(None, description="Deployment window start")
    deployment_window_end: datetime | None = Field(None, description="Deployment window end")


class UpdateProgressReport(BaseModel):
    """Schema for reporting update progress."""

    device_id: UUID = Field(..., description="Device identifier")
    update_id: UUID = Field(..., description="Update identifier")
    status: DeviceUpdateStatus = Field(..., description="Current update status")
    download_progress: float = Field(
        0.0, ge=0.0, le=100.0, description="Download progress percentage"
    )
    install_progress: float = Field(
        0.0, ge=0.0, le=100.0, description="Installation progress percentage"
    )
    error_message: str | None = Field(None, description="Error message if failed")
    battery_level: int | None = Field(None, ge=0, le=100, description="Current battery level")


class HeartbeatRequest(BaseModel):
    """Schema for device heartbeat."""

    device_id: UUID = Field(..., description="Device identifier")
    device_type: str = Field(..., description="Device type")
    hardware_model: str | None = Field(None, description="Hardware model")
    serial_number: str | None = Field(None, description="Device serial number")

    # Software versions
    firmware_version: str = Field(..., description="Current firmware version")
    application_version: str | None = Field(None, description="Current app version")
    bootloader_version: str | None = Field(None, description="Bootloader version")

    # System status
    uptime_seconds: int | None = Field(None, ge=0, description="Device uptime")
    battery_level: int | None = Field(None, ge=0, le=100, description="Battery level")
    charging_status: bool | None = Field(None, description="Charging status")
    cpu_usage_percent: float | None = Field(None, ge=0.0, le=100.0, description="CPU usage")
    memory_usage_percent: float | None = Field(None, ge=0.0, le=100.0, description="Memory usage")
    storage_used_mb: int | None = Field(None, ge=0, description="Used storage MB")
    storage_total_mb: int | None = Field(None, ge=0, description="Total storage MB")

    # Network status
    network_type: str | None = Field(None, description="Network type")
    signal_strength: int | None = Field(None, description="Signal strength")
    ip_address: str | None = Field(None, description="IP address")

    # Location (if available)
    latitude: float | None = Field(None, ge=-90.0, le=90.0, description="Latitude")
    longitude: float | None = Field(None, ge=-180.0, le=180.0, description="Longitude")
    location_accuracy: float | None = Field(None, ge=0.0, description="Location accuracy")

    # Update status
    pending_update_id: UUID | None = Field(None, description="Pending update ID")
    last_update_check: datetime | None = Field(None, description="Last update check")

    # Error reporting
    recent_errors: list[dict] | None = Field(None, description="Recent errors")
    crash_count_24h: int = Field(0, ge=0, description="Crashes in last 24h")
    last_crash_at: datetime | None = Field(None, description="Last crash timestamp")

    # Custom telemetry
    custom_metrics: dict | None = Field(None, description="Custom metrics")
    tags: dict | None = Field(None, description="Device tags")


class HeartbeatResponse(BaseModel):
    """Schema for heartbeat response."""

    heartbeat_id: UUID
    device_id: UUID
    received_at: datetime
    update_check_required: bool = Field(False, description="Device should check for updates")
    configuration_update: dict | None = Field(None, description="Configuration updates")
    commands: list[dict] | None = Field(None, description="Pending commands")

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic configuration."""

        from_attributes = True


class UpdateRolloutStatus(BaseModel):
    """Schema for update rollout status."""

    update_id: UUID
    deployment_ring: DeploymentRing
    total_devices: int
    pending_devices: int
    downloading_devices: int
    installing_devices: int
    completed_devices: int
    failed_devices: int
    success_rate: float
    failure_rate: float
    average_download_time_minutes: float | None
    average_install_time_minutes: float | None


class RollbackRequest(BaseModel):
    """Schema for initiating update rollback."""

    update_id: UUID = Field(..., description="Update to rollback")
    reason: str = Field(..., description="Rollback reason")
    target_rings: list[DeploymentRing] | None = Field(
        None, description="Specific rings to rollback (default: all)"
    )
    force_immediate: bool = Field(False, description="Force immediate rollback")


class UpdateListResponse(BaseModel):
    """Schema for update list response."""

    updates: list[FirmwareUpdateResponse]
    total: int
    page: int
    size: int
    pages: int


class DeviceListResponse(BaseModel):
    """Schema for device list response."""

    devices: list[dict]
    total: int
    page: int
    size: int
    pages: int


class UpdateMetrics(BaseModel):
    """Schema for update deployment metrics."""

    update_id: UUID
    total_devices_targeted: int
    devices_completed: int
    devices_failed: int
    devices_pending: int
    success_rate_percentage: float
    failure_rate_percentage: float
    average_deployment_time_hours: float | None
    rollback_triggered: bool
    rollback_reason: str | None


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    timestamp: datetime
    version: str
    dependencies: dict[str, str]
    metrics: dict[str, int | float] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    message: str
    details: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
