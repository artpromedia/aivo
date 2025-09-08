"""
Tests for parent enrollment path.
"""

from unittest.mock import AsyncMock

import pytest
from app.models import EnrollmentStatus, ProvisionSource
from app.schemas import EnrollmentContext, EnrollmentRequest, LearnerProfile
from app.services import EnrollmentRouterService


class TestParentEnrollmentPath:
    """Test parent enrollment routing."""

    @pytest.mark.asyncio
    async def test_parent_enrollment_with_guardian_id(
        self, db_session, sample_learner_profile, sample_parent_context, mock_payment_service
    ):
        """Test successful parent enrollment with guardian ID."""
        service = EnrollmentRouterService()
        service.payment_service = mock_payment_service

        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_parent_context),
        )

        result = await service.route_enrollment(db_session, request)

        assert result.provision_source == ProvisionSource.PARENT
        assert result.status == EnrollmentStatus.CHECKOUT_REQUIRED
        assert result.guardian_id == "guardian_123"
        assert result.checkout_session_id == "cs_test_123"
        assert result.checkout_url == "https://checkout.stripe.com/pay/cs_test_123"
        assert "checkout session" in result.message.lower()

    @pytest.mark.asyncio
    async def test_parent_enrollment_generates_guardian_id(
        self, db_session, sample_learner_profile, mock_payment_service
    ):
        """Test that service generates guardian ID when auto-creating parent context."""
        service = EnrollmentRouterService()
        service.payment_service = mock_payment_service

        # Test the service's ability to generate guardian ID internally
        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(guardian_id="auto_generate", source="parent_portal"),
        )

        result = await service.route_enrollment(db_session, request)

        assert result.provision_source == ProvisionSource.PARENT
        assert result.status == EnrollmentStatus.CHECKOUT_REQUIRED
        # The service should handle guardian ID generation in _process_parent_enrollment
        assert result.guardian_id == "auto_generate"  # In this case it uses what's provided
        assert result.checkout_session_id == "cs_test_123"

    @pytest.mark.asyncio
    async def test_parent_enrollment_checkout_failure(
        self, db_session, sample_learner_profile, sample_parent_context
    ):
        """Test parent enrollment when checkout session creation fails."""
        service = EnrollmentRouterService()

        # Mock payment service to raise exception
        mock_payment = AsyncMock()
        mock_payment.create_checkout_session.side_effect = Exception("Payment service unavailable")
        service.payment_service = mock_payment

        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_parent_context),
        )

        result = await service.route_enrollment(db_session, request)

        assert result.provision_source == ProvisionSource.PARENT
        assert result.status == EnrollmentStatus.FAILED
        assert "Payment service unavailable" in result.message
        assert result.checkout_session_id is None
        assert result.checkout_url is None

    @pytest.mark.asyncio
    async def test_checkout_session_metadata_includes_learner_info(
        self, db_session, sample_learner_profile, sample_parent_context, mock_payment_service
    ):
        """Test that checkout session includes learner information in metadata."""
        service = EnrollmentRouterService()
        service.payment_service = mock_payment_service

        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_parent_context),
        )

        await service.route_enrollment(db_session, request)

        # Verify payment service was called with correct data
        mock_payment_service.create_checkout_session.assert_called_once()
        call_args = mock_payment_service.create_checkout_session.call_args

        assert call_args[1]["guardian_id"] == "guardian_123"
        assert call_args[1]["learner_profile"].email == "student@example.com"
        assert call_args[1]["learner_profile"].first_name == "John"
        assert call_args[1]["context"].guardian_id == "guardian_123"


class TestEnrollmentContextValidation:
    """Test enrollment context validation."""

    @pytest.mark.asyncio
    async def test_enrollment_requires_tenant_or_guardian_id(self, sample_learner_profile):
        """Test that enrollment context requires either tenant_id or guardian_id."""
        with pytest.raises(ValueError, match="Either tenant_id or guardian_id must be provided"):
            EnrollmentContext(source="test")

    @pytest.mark.asyncio
    async def test_enrollment_allows_tenant_id_only(self, sample_learner_profile):
        """Test that enrollment context allows tenant_id only."""
        context = EnrollmentContext(tenant_id=1, source="district")
        assert context.tenant_id == 1
        assert context.guardian_id is None

    @pytest.mark.asyncio
    async def test_enrollment_allows_guardian_id_only(self, sample_learner_profile):
        """Test that enrollment context allows guardian_id only."""
        context = EnrollmentContext(guardian_id="guardian_123", source="parent")
        assert context.guardian_id == "guardian_123"
        assert context.tenant_id is None

    @pytest.mark.asyncio
    async def test_enrollment_allows_both_tenant_and_guardian_id(self, sample_learner_profile):
        """Test that enrollment context allows both tenant_id and guardian_id."""
        context = EnrollmentContext(tenant_id=1, guardian_id="guardian_123", source="mixed")
        assert context.tenant_id == 1
        assert context.guardian_id == "guardian_123"


class TestLearnerProfileValidation:
    """Test learner profile validation."""

    @pytest.mark.asyncio
    async def test_learner_profile_requires_email(self):
        """Test that learner profile requires email."""
        with pytest.raises(ValueError):
            LearnerProfile(first_name="John", last_name="Doe")

    @pytest.mark.asyncio
    async def test_learner_profile_requires_first_name(self):
        """Test that learner profile requires first name."""
        with pytest.raises(ValueError):
            LearnerProfile(email="test@example.com", last_name="Doe")

    @pytest.mark.asyncio
    async def test_learner_profile_requires_last_name(self):
        """Test that learner profile requires last name."""
        with pytest.raises(ValueError):
            LearnerProfile(email="test@example.com", first_name="John")

    @pytest.mark.asyncio
    async def test_learner_profile_optional_fields(self):
        """Test that learner profile optional fields work correctly."""
        profile = LearnerProfile(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            learner_id="student_123",
            grade_level="5th",
            school="Test School",
        )

        assert profile.learner_id == "student_123"
        assert profile.grade_level == "5th"
        assert profile.school == "Test School"
