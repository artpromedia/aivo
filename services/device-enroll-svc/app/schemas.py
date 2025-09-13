"""Pydantic schemas for Device Enrollment Service."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .models import AttestationStatus, DeviceStatus


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class EnrollmentRequest(BaseModel):
    """Device enrollment request."""

    serial_number: str = Field(
        ...,
        description="Device serial number",
        min_length=1,
        max_length=255,
    )
    hardware_fingerprint: str = Field(
        ...,
        description="Unique hardware fingerprint",
        min_length=1,
        max_length=512,
    )
    device_model: str = Field(
        default="aivo-pad",
        description="Device model identifier",
        max_length=100,
    )
    firmware_version: Optional[str] = Field(
        None,
        description="Device firmware version",
        max_length=50,
    )
    enrollment_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional enrollment metadata",
    )


class EnrollmentResponse(BaseModel):
    """Device enrollment response."""

    device_id: UUID = Field(..., description="Unique device identifier")
    status: DeviceStatus = Field(..., description="Enrollment status")
    bootstrap_token: str = Field(..., description="Bootstrap authentication token")
    bootstrap_expires_at: datetime = Field(..., description="Bootstrap token expiration")
    message: str = Field(..., description="Status message")


class AttestationChallengeRequest(BaseModel):
    """Request for attestation challenge."""

    device_id: UUID = Field(..., description="Device identifier")


class AttestationChallengeResponse(BaseModel):
    """Attestation challenge response."""

    challenge_id: UUID = Field(..., description="Challenge identifier")
    nonce: str = Field(..., description="Random nonce for signing")
    challenge_data: str = Field(..., description="Data to be signed")
    expires_at: datetime = Field(..., description="Challenge expiration time")


class AttestationSubmissionRequest(BaseModel):
    """Attestation submission request."""

    challenge_id: UUID = Field(..., description="Challenge identifier")
    signature: str = Field(..., description="Signed challenge data")
    public_key_pem: str = Field(..., description="Device public key in PEM format")
    attestation_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional attestation metadata",
    )


class AttestationSubmissionResponse(BaseModel):
    """Attestation submission response."""

    challenge_id: UUID = Field(..., description="Challenge identifier")
    status: AttestationStatus = Field(..., description="Attestation status")
    device_certificate_pem: Optional[str] = Field(
        None, description="Device certificate in PEM format"
    )
    certificate_serial: Optional[str] = Field(None, description="Certificate serial number")
    certificate_expires_at: Optional[datetime] = Field(
        None, description="Certificate expiration time"
    )
    message: str = Field(..., description="Status message")


class DeviceInfoResponse(BaseModel):
    """Device information response."""

    device_id: UUID = Field(..., description="Device identifier")
    serial_number: str = Field(..., description="Device serial number")
    device_model: str = Field(..., description="Device model")
    status: DeviceStatus = Field(..., description="Device status")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    certificate_serial: Optional[str] = Field(None, description="Certificate serial number")
    certificate_expires_at: Optional[datetime] = Field(None, description="Certificate expiration")
    last_seen_at: Optional[datetime] = Field(None, description="Last activity")
    created_at: datetime = Field(..., description="Enrollment date")


class DeviceListResponse(BaseModel):
    """Device list response."""

    devices: list[DeviceInfoResponse] = Field(..., description="List of devices")
    total: int = Field(..., description="Total device count")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")


class CertificateRevokeRequest(BaseModel):
    """Certificate revocation request."""

    device_id: UUID = Field(..., description="Device identifier")
    reason: str = Field(..., description="Revocation reason")


class CertificateRevokeResponse(BaseModel):
    """Certificate revocation response."""

    device_id: UUID = Field(..., description="Device identifier")
    status: DeviceStatus = Field(..., description="New device status")
    revoked_at: datetime = Field(..., description="Revocation timestamp")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    database: str = Field(..., description="Database status")


# Fleet Health Schemas

class FleetHealthResponse(BaseModel):
    """Fleet health metrics response."""

    summary: Dict[str, Any] = Field(..., description="Fleet health summary")
    status_distribution: Dict[str, int] = Field(..., description="Device status counts")
    firmware_drift: list[Dict[str, Any]] = Field(..., description="Firmware version distribution")
    health_trends: list[Dict[str, Any]] = Field(..., description="Health trends over time")
    alerts: Dict[str, list] = Field(..., description="Active alerts")


# Alert Rule Schemas

class AlertRuleRequest(BaseModel):
    """Alert rule creation/update request."""

    name: str = Field(..., description="Alert rule name", max_length=255)
    description: Optional[str] = Field(None, description="Alert rule description")
    metric: str = Field(..., description="Metric to monitor", max_length=100)
    condition: str = Field(..., description="Alert condition")
    threshold: str = Field(..., description="Alert threshold value", max_length=100)
    window_minutes: int = Field(15, description="Evaluation window in minutes", ge=1, le=1440)
    tenant_id: Optional[UUID] = Field(None, description="Tenant filter")
    device_filter: Optional[Dict[str, Any]] = Field(None, description="Device selection criteria")
    actions: list[str] = Field(..., description="Actions to execute")
    action_config: Optional[Dict[str, Any]] = Field(None, description="Action configuration")
    is_enabled: bool = Field(True, description="Whether rule is enabled")


class AlertRuleResponse(BaseModel):
    """Alert rule response."""

    rule_id: UUID = Field(..., description="Alert rule ID")
    name: str = Field(..., description="Alert rule name")
    description: Optional[str] = Field(None, description="Alert rule description")
    metric: str = Field(..., description="Metric being monitored")
    condition: str = Field(..., description="Alert condition")
    threshold: str = Field(..., description="Alert threshold")
    window_minutes: int = Field(..., description="Evaluation window")
    tenant_id: Optional[UUID] = Field(None, description="Tenant filter")
    device_filter: Optional[Dict[str, Any]] = Field(None, description="Device filter")
    actions: list[str] = Field(..., description="Configured actions")
    action_config: Optional[Dict[str, Any]] = Field(None, description="Action config")
    is_enabled: bool = Field(..., description="Whether rule is enabled")
    trigger_count: int = Field(..., description="Number of times triggered")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger time")
    created_by: UUID = Field(..., description="Creator user ID")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")


class AlertRuleListResponse(BaseModel):
    """Alert rule list response."""

    rules: list[AlertRuleResponse] = Field(..., description="Alert rules")
    total: int = Field(..., description="Total rule count")


class AlertTriggerResponse(BaseModel):
    """Alert trigger response."""

    trigger_id: UUID = Field(..., description="Trigger ID")
    rule_id: UUID = Field(..., description="Alert rule ID")
    rule_name: str = Field(..., description="Alert rule name")
    metric_value: str = Field(..., description="Metric value at trigger")
    affected_devices: Optional[list[str]] = Field(None, description="Affected device IDs")
    trigger_reason: str = Field(..., description="Trigger reason")
    actions_executed: Optional[list[str]] = Field(None, description="Executed actions")
    action_results: Optional[Dict[str, Any]] = Field(None, description="Action results")
    triggered_at: datetime = Field(..., description="Trigger time")


class AlertMetricsResponse(BaseModel):
    """Available alert metrics response."""

    metrics: list[Dict[str, str]] = Field(..., description="Available metrics")
    conditions: list[Dict[str, str]] = Field(..., description="Available conditions")
    actions: list[Dict[str, str]] = Field(..., description="Available actions")


# Device Action Schemas

class DeviceActionRequest(BaseModel):
    """Device action request."""

    action_type: str = Field(..., description="Action type (wipe, reboot, lock)")
    reason: Optional[str] = Field(None, description="Action reason")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")


class DeviceActionResponse(BaseModel):
    """Device action response."""

    action_id: UUID = Field(..., description="Action ID")
    device_id: UUID = Field(..., description="Device ID")
    action_type: str = Field(..., description="Action type")
    status: str = Field(..., description="Action status")
    reason: Optional[str] = Field(None, description="Action reason")
    initiated_by: UUID = Field(..., description="User who initiated action")
    created_at: datetime = Field(..., description="Action creation time")
    sent_at: Optional[datetime] = Field(None, description="Action sent time")
    completed_at: Optional[datetime] = Field(None, description="Action completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
