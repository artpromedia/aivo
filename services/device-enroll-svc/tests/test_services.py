"""Tests for Device Enrollment Service."""
# pylint: disable=redefined-outer-name

from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models import Device, DeviceStatus
from app.services import AttestationService, DeviceEnrollmentService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def enrollment_service():
    """Create DeviceEnrollmentService instance."""
    return DeviceEnrollmentService()


@pytest.fixture
def attestation_service():
    """Create AttestationService instance."""
    return AttestationService()


@pytest.fixture
def sample_device():
    """Sample device for testing."""
    return Device(
        device_id=uuid4(),
        serial_number="APD-2024-001234",
        hardware_fingerprint="sha256:a1b2c3d4e5f6...",
        device_model="aivo-pad",
        firmware_version="1.0.2",
        status=DeviceStatus.PENDING,
        bootstrap_token="test-token",
        bootstrap_expires_at=datetime.utcnow() + timedelta(hours=24),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestDeviceEnrollmentService:
    """Test DeviceEnrollmentService."""

    async def test_enroll_device_success(
        self, enrollment_service, mock_db, sample_device
    ):
        """Test successful device enrollment."""
        # Mock database operations
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Test enrollment
        result = await enrollment_service.enroll_device(
            serial_number="APD-2024-001234",
            hardware_fingerprint="sha256:a1b2c3d4e5f6...",
            db=mock_db,
        )

        # Assertions
        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called

    async def test_enroll_duplicate_device(
        self, enrollment_service, mock_db, sample_device
    ):
        """Test enrollment of duplicate device."""
        # Mock existing device
        mock_db.execute.return_value.scalar_one_or_none.return_value = (
            sample_device
        )

        # Test enrollment should raise error
        with pytest.raises(ValueError, match="already enrolled"):
            await enrollment_service.enroll_device(
                serial_number="APD-2024-001234",
                hardware_fingerprint="sha256:a1b2c3d4e5f6...",
                db=mock_db,
            )


class TestAttestationService:
    """Test AttestationService."""

    async def test_create_challenge_success(
        self, attestation_service, mock_db, sample_device
    ):
        """Test successful challenge creation."""
        # Mock device lookup
        mock_db.execute.return_value.scalar_one_or_none.return_value = (
            sample_device
        )
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Test challenge creation
        result = await attestation_service.create_challenge(
            device_id=sample_device.device_id,
            db=mock_db,
        )

        # Assertions
        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called

    async def test_create_challenge_device_not_found(
        self, attestation_service, mock_db
    ):
        """Test challenge creation for non-existent device."""
        # Mock no device found
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        # Test should raise error
        with pytest.raises(ValueError, match="Device not found"):
            await attestation_service.create_challenge(
                device_id=uuid4(),
                db=mock_db,
            )
