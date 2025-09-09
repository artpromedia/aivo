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
    bootstrap_token: str = Field(
        ..., description="Bootstrap authentication token"
    )
    bootstrap_expires_at: datetime = Field(
        ..., description="Bootstrap token expiration"
    )
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
    public_key_pem: str = Field(
        ..., description="Device public key in PEM format"
    )
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
    certificate_serial: Optional[str] = Field(
        None, description="Certificate serial number"
    )
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
    firmware_version: Optional[str] = Field(
        None, description="Firmware version"
    )
    certificate_serial: Optional[str] = Field(
        None, description="Certificate serial number"
    )
    certificate_expires_at: Optional[datetime] = Field(
        None, description="Certificate expiration"
    )
    last_seen_at: Optional[datetime] = Field(None, description="Last activity")
    created_at: datetime = Field(..., description="Enrollment date")


class DeviceListResponse(BaseModel):
    """Device list response."""

    devices: list[DeviceInfoResponse] = Field(
        ..., description="List of devices"
    )
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
