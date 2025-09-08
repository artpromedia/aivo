"""
Tests for district enrollment path.
"""

import pytest
from app.models import EnrollmentStatus, ProvisionSource
from app.schemas import EnrollmentContext, EnrollmentRequest, LearnerProfile
from app.services import DistrictSeatService, EnrollmentRouterService


class TestDistrictEnrollmentPath:
    """Test district enrollment routing."""

    @pytest.mark.asyncio
    async def test_district_enrollment_with_available_seats(
        self, db_session, district_allocation, sample_learner_profile, sample_district_context
    ):
        """Test successful district enrollment when seats are available."""
        service = EnrollmentRouterService()

        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_district_context),
        )

        result = await service.route_enrollment(db_session, request)

        assert result.provision_source == ProvisionSource.DISTRICT
        assert result.status == EnrollmentStatus.COMPLETED
        assert result.tenant_id == 1
        assert result.seats_reserved == 1
        assert result.seats_available == 69  # 100 - 20 - 10 - 1 reserved
        assert "district allocation" in result.message.lower()

    @pytest.mark.asyncio
    async def test_district_enrollment_no_seats_fallback_to_parent(
        self, db_session, sample_learner_profile, sample_district_context, mock_payment_service
    ):
        """Test fallback to parent payment when no district seats available."""
        # Create allocation with no available seats
        district_service = DistrictSeatService()
        await district_service.create_allocation(db_session, 1, 0)

        service = EnrollmentRouterService()
        service.payment_service = mock_payment_service

        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_district_context),
        )

        result = await service.route_enrollment(db_session, request)

        assert result.provision_source == ProvisionSource.PARENT
        assert result.status == EnrollmentStatus.CHECKOUT_REQUIRED
        assert result.checkout_session_id == "cs_test_123"
        assert result.checkout_url == "https://checkout.stripe.com/pay/cs_test_123"

    @pytest.mark.asyncio
    async def test_district_enrollment_no_allocation_fallback_to_parent(
        self, db_session, sample_learner_profile, sample_district_context, mock_payment_service
    ):
        """Test fallback to parent payment when no district allocation exists."""
        service = EnrollmentRouterService()
        service.payment_service = mock_payment_service

        request = EnrollmentRequest(
            learner_profile=LearnerProfile(**sample_learner_profile),
            context=EnrollmentContext(**sample_district_context),
        )

        result = await service.route_enrollment(db_session, request)

        assert result.provision_source == ProvisionSource.PARENT
        assert result.status == EnrollmentStatus.CHECKOUT_REQUIRED

    @pytest.mark.asyncio
    async def test_seat_reservation_updates_allocation(self, db_session, district_allocation):
        """Test that seat reservation properly updates allocation."""
        initial_reserved = district_allocation.reserved_seats
        initial_available = district_allocation.available_seats

        district_service = DistrictSeatService()
        success = await district_service.reserve_seats(db_session, 1, 2)

        assert success is True

        # Refresh allocation to get updated values
        await db_session.refresh(district_allocation)

        assert district_allocation.reserved_seats == initial_reserved + 2
        assert district_allocation.available_seats == initial_available - 2

    @pytest.mark.asyncio
    async def test_cannot_reserve_more_seats_than_available(self, db_session, district_allocation):
        """Test that cannot reserve more seats than available."""
        district_service = DistrictSeatService()

        # Try to reserve more seats than available (70 available, try to reserve 100)
        success = await district_service.reserve_seats(db_session, 1, 100)

        assert success is False

        # Allocation should be unchanged
        await db_session.refresh(district_allocation)
        assert district_allocation.reserved_seats == 10  # Original value


class TestDistrictSeatManagement:
    """Test district seat allocation management."""

    @pytest.mark.asyncio
    async def test_create_district_allocation(self, db_session):
        """Test creating a new district seat allocation."""
        district_service = DistrictSeatService()

        allocation = await district_service.create_allocation(
            db_session, tenant_id=2, total_seats=50
        )

        assert allocation.tenant_id == 2
        assert allocation.total_seats == 50
        assert allocation.reserved_seats == 0
        assert allocation.used_seats == 0
        assert allocation.available_seats == 50
        assert allocation.is_active is True

    @pytest.mark.asyncio
    async def test_get_allocation_by_tenant(self, db_session, district_allocation):
        """Test retrieving allocation by tenant ID."""
        district_service = DistrictSeatService()

        found_allocation = await district_service.get_allocation(db_session, 1)

        assert found_allocation is not None
        assert found_allocation.id == district_allocation.id
        assert found_allocation.tenant_id == 1

    @pytest.mark.asyncio
    async def test_has_available_seats_check(self, db_session, district_allocation):
        """Test checking for available seats."""
        district_service = DistrictSeatService()

        # Should have available seats (70 available)
        has_seats = await district_service.has_available_seats(db_session, 1, 50)
        assert has_seats is True

        # Should not have enough seats
        has_seats = await district_service.has_available_seats(db_session, 1, 100)
        assert has_seats is False

    @pytest.mark.asyncio
    async def test_has_available_seats_nonexistent_tenant(self, db_session):
        """Test checking seats for nonexistent tenant."""
        district_service = DistrictSeatService()

        has_seats = await district_service.has_available_seats(db_session, 999, 1)
        assert has_seats is False
