"""FastAPI routes for Device Enrollment Service."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Device
from .schemas import (
    AttestationChallengeRequest,
    AttestationChallengeResponse,
    AttestationSubmissionRequest,
    AttestationSubmissionResponse,
    CertificateRevokeRequest,
    CertificateRevokeResponse,
    DeviceInfoResponse,
    DeviceListResponse,
    EnrollmentRequest,
    EnrollmentResponse,
    ErrorResponse,
    HealthResponse,
)
from .services import AttestationService, DeviceEnrollmentService

logger = structlog.get_logger(__name__)

router = APIRouter()

# Service instances
enrollment_service = DeviceEnrollmentService()
attestation_service = AttestationService()


@router.post(
    "/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll Aivo Pad Device",
    description="Enroll a new Aivo Pad device and issue bootstrap token",
    responses={
        201: {"description": "Device enrolled successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        409: {"model": ErrorResponse, "description": "Device already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def enroll_device(
    request: EnrollmentRequest,
    req: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnrollmentResponse:
    """Enroll a new Aivo Pad device."""
    try:
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")

        device = await enrollment_service.enroll_device(
            serial_number=request.serial_number,
            hardware_fingerprint=request.hardware_fingerprint,
            db=db,
            device_model=request.device_model,
            firmware_version=request.firmware_version,
            enrollment_data=request.enrollment_data,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        return EnrollmentResponse(
            device_id=device.device_id,
            status=device.status,
            bootstrap_token=device.bootstrap_token,
            bootstrap_expires_at=device.bootstrap_expires_at,
            message="Device enrolled successfully",
        )

    except ValueError as e:
        logger.warning(
            "Device enrollment failed",
            serial=request.serial_number,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(
            "Device enrollment error",
            serial=request.serial_number,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.post(
    "/attest/challenge",
    response_model=AttestationChallengeResponse,
    summary="Request Attestation Challenge",
    description="Request an attestation challenge for device verification",
    responses={
        200: {"description": "Challenge created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Device not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_attestation_challenge(
    request: AttestationChallengeRequest,
    req: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttestationChallengeResponse:
    """Create an attestation challenge for a device."""
    try:
        client_ip = req.client.host if req.client else None

        challenge = await attestation_service.create_challenge(
            device_id=request.device_id,
            db=db,
            client_ip=client_ip,
        )

        return AttestationChallengeResponse(
            challenge_id=challenge.challenge_id,
            nonce=challenge.nonce,
            challenge_data=challenge.challenge_data,
            expires_at=challenge.expires_at,
        )

    except ValueError as e:
        logger.warning(
            "Challenge creation failed",
            device_id=request.device_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(
            "Challenge creation error",
            device_id=request.device_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.post(
    "/attest",
    response_model=AttestationSubmissionResponse,
    summary="Submit Attestation",
    description="Submit signed attestation challenge and receive certificate",
    responses={
        200: {"description": "Attestation verified successfully"},
        400: {"model": ErrorResponse, "description": "Invalid attestation"},
        404: {"model": ErrorResponse, "description": "Challenge not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def submit_attestation(
    request: AttestationSubmissionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttestationSubmissionResponse:
    """Submit attestation and receive device certificate."""
    try:
        challenge, certificate_pem = (
            await attestation_service.verify_attestation(
                challenge_id=request.challenge_id,
                signature=request.signature,
                public_key_pem=request.public_key_pem,
                db=db,
                attestation_data=request.attestation_data,
            )
        )

        # Get updated device info for certificate details
        device = await enrollment_service.get_device_by_id(
            challenge.device_id, db
        )

        return AttestationSubmissionResponse(
            challenge_id=challenge.challenge_id,
            status=challenge.status,
            device_certificate_pem=certificate_pem,
            certificate_serial=device.certificate_serial if device else None,
            certificate_expires_at=(
                device.certificate_expires_at if device else None
            ),
            message=(
                "Attestation verified and certificate issued"
                if certificate_pem
                else "Attestation verification failed"
            ),
        )

    except ValueError as e:
        logger.warning(
            "Attestation submission failed",
            challenge_id=request.challenge_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(
            "Attestation submission error",
            challenge_id=request.challenge_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/devices/{device_id}",
    response_model=DeviceInfoResponse,
    summary="Get Device Information",
    description="Get detailed information about a specific device",
    responses={
        200: {"description": "Device information retrieved"},
        404: {"model": ErrorResponse, "description": "Device not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_device_info(
    device_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DeviceInfoResponse:
    """Get device information by ID."""
    try:
        device = await enrollment_service.get_device_by_id(device_id, db)

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        return DeviceInfoResponse(
            device_id=device.device_id,
            serial_number=device.serial_number,
            device_model=device.device_model,
            status=device.status,
            firmware_version=device.firmware_version,
            certificate_serial=device.certificate_serial,
            certificate_expires_at=device.certificate_expires_at,
            last_seen_at=device.last_seen_at,
            created_at=device.created_at,
        )

    except HTTPException:
        raise

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(
            "Get device info error",
            device_id=device_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/devices",
    response_model=DeviceListResponse,
    summary="List Devices",
    description="Get paginated list of enrolled devices",
    responses={
        200: {"description": "Device list retrieved"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_devices(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    size: int = 50,
) -> DeviceListResponse:
    """List enrolled devices with pagination."""
    try:
        # Validate pagination parameters
        page = max(1, page)
        size = max(1, min(100, size))
        offset = (page - 1) * size

        # Get total count
        count_result = await db.execute(select(func.count(Device.device_id)))
        total = count_result.scalar()

        # Get devices
        result = await db.execute(
            select(Device)
            .order_by(Device.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        devices = result.scalars().all()

        device_list = [
            DeviceInfoResponse(
                device_id=device.device_id,
                serial_number=device.serial_number,
                device_model=device.device_model,
                status=device.status,
                firmware_version=device.firmware_version,
                certificate_serial=device.certificate_serial,
                certificate_expires_at=device.certificate_expires_at,
                last_seen_at=device.last_seen_at,
                created_at=device.created_at,
            )
            for device in devices
        ]

        return DeviceListResponse(
            devices=device_list,
            total=total,
            page=page,
            size=size,
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("List devices error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.post(
    "/devices/{device_id}/revoke",
    response_model=CertificateRevokeResponse,
    summary="Revoke Device Certificate",
    description="Revoke a device certificate and disable the device",
    responses={
        200: {"description": "Certificate revoked successfully"},
        404: {"model": ErrorResponse, "description": "Device not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def revoke_device_certificate(
    device_id: UUID,
    request: CertificateRevokeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CertificateRevokeResponse:
    """Revoke a device certificate."""
    try:
        device = await attestation_service.revoke_device(
            device_id=device_id,
            reason=request.reason,
            db=db,
        )

        return CertificateRevokeResponse(
            device_id=device.device_id,
            status=device.status,
            revoked_at=device.updated_at,
            message=f"Device certificate revoked: {request.reason}",
        )

    except ValueError as e:
        logger.warning(
            "Certificate revocation failed",
            device_id=device_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(
            "Certificate revocation error",
            device_id=device_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check service health and database connectivity",
    responses={
        200: {"description": "Service is healthy"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    },
)
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HealthResponse:
    """Health check endpoint."""
    try:
        # Test database connectivity
        await db.execute(select(1))
        db_status = "healthy"

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Health check database error", error=str(e))
        db_status = "unhealthy"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connectivity issues",
        ) from e

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database=db_status,
    )
