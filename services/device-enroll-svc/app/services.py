"""Business logic services for Device Enrollment."""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import structlog
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.x509 import (
    CertificateBuilder,
    Name,
    NameAttribute,
    random_serial_number,
)
from cryptography.x509.oid import NameOID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    AttestationChallenge,
    AttestationStatus,
    Device,
    DeviceStatus,
)

logger = structlog.get_logger(__name__)


class DeviceEnrollmentService:
    """Service for device enrollment operations."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.bootstrap_token_lifetime = timedelta(hours=24)
        self.challenge_lifetime = timedelta(minutes=15)

    async def enroll_device(
        self,
        serial_number: str,
        hardware_fingerprint: str,
        db: AsyncSession,
        device_model: str = "aivo-pad",
        firmware_version: Optional[str] = None,
        enrollment_data: Optional[dict] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Device:
        """Enroll a new device."""
        # Check if device already exists
        result = await db.execute(
            select(Device).where(Device.serial_number == serial_number)
        )
        existing_device = result.scalar_one_or_none()

        if existing_device:
            if existing_device.status == DeviceStatus.REVOKED:
                raise ValueError(
                    "Device has been revoked and cannot be re-enrolled"
                )
            if existing_device.status in [
                DeviceStatus.ENROLLED,
                DeviceStatus.ATTESTED,
            ]:
                logger.info(
                    "Device already enrolled",
                    device_id=existing_device.device_id,
                    serial=serial_number,
                    status=existing_device.status,
                )
                return existing_device

        # Generate bootstrap token
        bootstrap_token = self._generate_bootstrap_token()
        bootstrap_expires_at = (
            datetime.utcnow() + self.bootstrap_token_lifetime
        )

        if existing_device:
            # Update existing device
            await db.execute(
                update(Device)
                .where(Device.device_id == existing_device.device_id)
                .values(
                    hardware_fingerprint=hardware_fingerprint,
                    device_model=device_model,
                    firmware_version=firmware_version,
                    status=DeviceStatus.ENROLLED,
                    enrollment_data=enrollment_data,
                    bootstrap_token=bootstrap_token,
                    bootstrap_expires_at=bootstrap_expires_at,
                    enrollment_ip=client_ip,
                    user_agent=user_agent,
                    last_seen_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            await db.commit()
            await db.refresh(existing_device)
            device = existing_device
        else:
            # Create new device
            device = Device(
                serial_number=serial_number,
                hardware_fingerprint=hardware_fingerprint,
                device_model=device_model,
                firmware_version=firmware_version,
                status=DeviceStatus.ENROLLED,
                enrollment_data=enrollment_data,
                bootstrap_token=bootstrap_token,
                bootstrap_expires_at=bootstrap_expires_at,
                enrollment_ip=client_ip,
                user_agent=user_agent,
                last_seen_at=datetime.utcnow(),
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)

        logger.info(
            "Device enrolled successfully",
            device_id=device.device_id,
            serial=serial_number,
            model=device_model,
            client_ip=client_ip,
        )

        return device

    def _generate_bootstrap_token(self) -> str:
        """Generate a secure bootstrap token."""
        return secrets.token_urlsafe(32)

    async def get_device_by_id(
        self, device_id: UUID, db: AsyncSession
    ) -> Optional[Device]:
        """Get device by ID."""
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        return result.scalar_one_or_none()

    async def get_device_by_serial(
        self, serial_number: str, db: AsyncSession
    ) -> Optional[Device]:
        """Get device by serial number."""
        result = await db.execute(
            select(Device).where(Device.serial_number == serial_number)
        )
        return result.scalar_one_or_none()


class AttestationService:
    """Service for device attestation operations."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.challenge_lifetime = timedelta(minutes=15)
        self.certificate_lifetime = timedelta(days=365)

    async def create_challenge(
        self,
        device_id: UUID,
        db: AsyncSession,
        client_ip: Optional[str] = None,
    ) -> AttestationChallenge:
        """Create an attestation challenge for a device."""
        # Verify device exists and is enrolled
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError("Device not found")

        if device.status not in [DeviceStatus.ENROLLED, DeviceStatus.ATTESTED]:
            raise ValueError(
                f"Device not eligible for attestation: {device.status}"
            )

        # Generate challenge data
        nonce = secrets.token_hex(32)
        timestamp = int(datetime.utcnow().timestamp())
        challenge_data = (
            f"aivo-pad-attestation:{device_id}:{nonce}:{timestamp}"
        )

        # Create challenge record
        challenge = AttestationChallenge(
            device_id=device_id,
            nonce=nonce,
            challenge_data=challenge_data,
            expires_at=datetime.utcnow() + self.challenge_lifetime,
            client_ip=client_ip,
        )

        db.add(challenge)
        await db.commit()
        await db.refresh(challenge)

        logger.info(
            "Attestation challenge created",
            challenge_id=challenge.challenge_id,
            device_id=device_id,
            expires_at=challenge.expires_at,
        )

        return challenge

    async def verify_attestation(
        self,
        challenge_id: UUID,
        signature: str,
        public_key_pem: str,
        db: AsyncSession,
        attestation_data: Optional[dict] = None,
    ) -> tuple[AttestationChallenge, Optional[str]]:
        """Verify attestation submission and issue certificate if valid."""
        # Get challenge
        result = await db.execute(
            select(AttestationChallenge).where(
                AttestationChallenge.challenge_id == challenge_id
            )
        )
        challenge = result.scalar_one_or_none()

        if not challenge:
            raise ValueError("Challenge not found")

        if challenge.status != AttestationStatus.PENDING:
            raise ValueError(
                f"Challenge already processed: {challenge.status}"
            )

        if datetime.utcnow() > challenge.expires_at:
            await db.execute(
                update(AttestationChallenge)
                .where(AttestationChallenge.challenge_id == challenge_id)
                .values(
                    status=AttestationStatus.EXPIRED,
                    completed_at=datetime.utcnow(),
                )
            )
            await db.commit()
            raise ValueError("Challenge has expired")

        # Verify signature
        try:
            public_key = load_pem_public_key(public_key_pem.encode())
            challenge_bytes = challenge.challenge_data.encode()
            signature_bytes = bytes.fromhex(signature)

            public_key.verify(
                signature_bytes,
                challenge_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            verification_status = AttestationStatus.VERIFIED
            certificate_pem = await self._issue_device_certificate(
                challenge.device_id, public_key_pem, db
            )

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning(
                "Attestation verification failed",
                challenge_id=challenge_id,
                error=str(e),
            )
            verification_status = AttestationStatus.FAILED
            certificate_pem = None

        # Update challenge status
        await db.execute(
            update(AttestationChallenge)
            .where(AttestationChallenge.challenge_id == challenge_id)
            .values(
                status=verification_status,
                signature=signature,
                attestation_data=attestation_data,
                verification_result={
                    "verified": (
                        verification_status == AttestationStatus.VERIFIED
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                completed_at=datetime.utcnow(),
            )
        )
        await db.commit()
        await db.refresh(challenge)

        logger.info(
            "Attestation verification completed",
            challenge_id=challenge_id,
            device_id=challenge.device_id,
            status=verification_status,
            certificate_issued=certificate_pem is not None,
        )

        return challenge, certificate_pem

    async def _issue_device_certificate(
        self, device_id: UUID, public_key_pem: str, db: AsyncSession
    ) -> str:
        """Issue a device certificate."""
        # Load device public key
        public_key = load_pem_public_key(public_key_pem.encode())

        # Generate CA private key
        # (in production, this should be stored securely)
        ca_private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )

        # Create certificate
        subject = Name(
            [
                NameAttribute(NameOID.COMMON_NAME, f"aivo-pad-{device_id}"),
                NameAttribute(NameOID.ORGANIZATION_NAME, "Aivo Technologies"),
                NameAttribute(
                    NameOID.ORGANIZATIONAL_UNIT_NAME, "Device Certificates"
                ),
            ]
        )        # In production, this should be the CA certificate subject
        issuer = Name(
            [
                NameAttribute(NameOID.COMMON_NAME, "Aivo Device CA"),
                NameAttribute(NameOID.ORGANIZATION_NAME, "Aivo Technologies"),
            ]
        )

        certificate_serial = str(random_serial_number())
        now = datetime.utcnow()
        cert = (
            CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(public_key)
            .serial_number(int(certificate_serial))
            .not_valid_before(now)
            .not_valid_after(now + self.certificate_lifetime)
            .sign(ca_private_key, hashes.SHA256())
        )

        certificate_pem = cert.public_bytes(
            serialization.Encoding.PEM
        ).decode()

        # Update device with certificate info
        await db.execute(
            update(Device)
            .where(Device.device_id == device_id)
            .values(
                status=DeviceStatus.ATTESTED,
                public_key_pem=public_key_pem,
                device_certificate_pem=certificate_pem,
                certificate_serial=certificate_serial,
                certificate_issued_at=now,
                certificate_expires_at=now + self.certificate_lifetime,
                last_seen_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()

        return certificate_pem

    async def revoke_device(
        self, device_id: UUID, reason: str, db: AsyncSession
    ) -> Device:
        """Revoke a device certificate."""
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            raise ValueError("Device not found")

        await db.execute(
            update(Device)
            .where(Device.device_id == device_id)
            .values(
                status=DeviceStatus.REVOKED,
                updated_at=datetime.utcnow(),
            )
        )
        await db.commit()
        await db.refresh(device)

        logger.info(
            "Device revoked",
            device_id=device_id,
            reason=reason,
            serial=device.serial_number,
        )

        return device
