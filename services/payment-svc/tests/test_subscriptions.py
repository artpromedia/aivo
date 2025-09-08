"""
Tests for subscription service functionality.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from app.models import PlanType, SubscriptionStatus
from app.schemas import CheckoutSessionCreate, TrialStartRequest


class TestSubscriptionService:
    """Test subscription management."""

    @pytest.mark.asyncio
    async def test_start_trial(self, subscription_service, db_session):
        """Test starting a trial subscription."""
        request = TrialStartRequest(tenant_id=1, seats=5)

        subscription = await subscription_service.start_trial(db_session, request)

        assert subscription.tenant_id == 1
        assert subscription.seats == 5
        assert subscription.plan_type == PlanType.MONTHLY
        assert subscription.status == SubscriptionStatus.TRIAL
        assert subscription.trial_start is not None
        assert subscription.trial_end is not None

        # Check trial duration
        trial_duration = subscription.trial_end - subscription.trial_start
        assert trial_duration.days == 14

    @pytest.mark.asyncio
    async def test_start_guardian_trial(self, subscription_service, db_session):
        """Test starting a trial for a guardian."""
        request = TrialStartRequest(guardian_id="guardian123", seats=3)

        subscription = await subscription_service.start_trial(db_session, request)

        assert subscription.guardian_id == "guardian123"
        assert subscription.tenant_id is None
        assert subscription.seats == 3
        assert subscription.status == SubscriptionStatus.TRIAL

    @pytest.mark.asyncio
    async def test_create_checkout_session(
        self, subscription_service, db_session, mock_stripe_service
    ):
        """Test creating a checkout session."""
        request = CheckoutSessionCreate(
            tenant_id=1,
            plan_type=PlanType.YEARLY,
            seats=10,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            has_sibling_discount=True,
        )

        (
            session_id,
            session_url,
            subscription_id,
        ) = await subscription_service.create_checkout_session(db_session, request)

        assert session_id == "cs_test123"
        assert session_url == "https://checkout.stripe.com/pay/cs_test123"
        assert subscription_id is not None

        # Verify Stripe service calls
        mock_stripe_service.create_customer.assert_called_once()
        mock_stripe_service.create_price.assert_called_once()
        mock_stripe_service.create_checkout_session.assert_called_once()

        # Check subscription record
        subscription = await subscription_service.get_subscription_by_id(
            db_session, subscription_id
        )
        assert subscription.status == SubscriptionStatus.INCOMPLETE
        assert subscription.plan_type == PlanType.YEARLY
        assert subscription.seats == 10
        assert subscription.discounted_amount < subscription.base_amount  # Should have discounts

    @pytest.mark.asyncio
    async def test_get_subscription_by_id(self, subscription_service, db_session):
        """Test retrieving subscription by ID."""
        # First create a subscription
        request = TrialStartRequest(tenant_id=1, seats=5)
        created_subscription = await subscription_service.start_trial(db_session, request)

        # Retrieve it
        retrieved_subscription = await subscription_service.get_subscription_by_id(
            db_session, created_subscription.id
        )

        assert retrieved_subscription is not None
        assert retrieved_subscription.id == created_subscription.id
        assert retrieved_subscription.tenant_id == 1
        assert retrieved_subscription.seats == 5

    @pytest.mark.asyncio
    async def test_get_nonexistent_subscription(self, subscription_service, db_session):
        """Test retrieving non-existent subscription."""
        subscription = await subscription_service.get_subscription_by_id(db_session, 99999)
        assert subscription is None

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_tenant(self, subscription_service, db_session):
        """Test retrieving subscriptions by tenant."""
        # Create multiple subscriptions for the same tenant
        request1 = TrialStartRequest(tenant_id=1, seats=3)
        request2 = TrialStartRequest(tenant_id=1, seats=5)
        request3 = TrialStartRequest(tenant_id=2, seats=7)  # Different tenant

        await subscription_service.start_trial(db_session, request1)
        await subscription_service.start_trial(db_session, request2)
        await subscription_service.start_trial(db_session, request3)

        # Get subscriptions for tenant 1
        tenant_subscriptions = await subscription_service.get_subscriptions_by_tenant(db_session, 1)

        assert len(tenant_subscriptions) == 2
        assert all(sub.tenant_id == 1 for sub in tenant_subscriptions)

        # Check seat counts
        seat_counts = {sub.seats for sub in tenant_subscriptions}
        assert seat_counts == {3, 5}

    @pytest.mark.asyncio
    async def test_get_subscriptions_by_guardian(self, subscription_service, db_session):
        """Test retrieving subscriptions by guardian."""
        # Create subscriptions for different guardians
        request1 = TrialStartRequest(guardian_id="guardian1", seats=2)
        request2 = TrialStartRequest(guardian_id="guardian1", seats=4)
        request3 = TrialStartRequest(guardian_id="guardian2", seats=6)

        await subscription_service.start_trial(db_session, request1)
        await subscription_service.start_trial(db_session, request2)
        await subscription_service.start_trial(db_session, request3)

        # Get subscriptions for guardian1
        guardian_subscriptions = await subscription_service.get_subscriptions_by_guardian(
            db_session, "guardian1"
        )

        assert len(guardian_subscriptions) == 2
        assert all(sub.guardian_id == "guardian1" for sub in guardian_subscriptions)

        # Check seat counts
        seat_counts = {sub.seats for sub in guardian_subscriptions}
        assert seat_counts == {2, 4}

    @pytest.mark.asyncio
    async def test_update_subscription_from_stripe(self, subscription_service, db_session):
        """Test updating subscription from Stripe data."""
        # Create a subscription
        request = TrialStartRequest(tenant_id=1, seats=5)
        subscription = await subscription_service.start_trial(db_session, request)

        # Mock Stripe subscription data
        stripe_subscription = Mock()
        stripe_subscription.id = "sub_test123"
        stripe_subscription.status = "active"
        stripe_subscription.current_period_start = 1640995200  # 2022-01-01
        stripe_subscription.current_period_end = 1643673600  # 2022-02-01
        stripe_subscription.trial_start = None
        stripe_subscription.trial_end = None
        stripe_subscription.canceled_at = None

        # Update subscription
        updated_subscription = await subscription_service.update_subscription_from_stripe(
            db_session, subscription.id, stripe_subscription
        )

        assert updated_subscription.stripe_subscription_id == "sub_test123"
        assert updated_subscription.status == SubscriptionStatus.ACTIVE
        assert updated_subscription.current_period_start == datetime(2022, 1, 1)
        assert updated_subscription.current_period_end == datetime(2022, 2, 1)

    def test_map_stripe_status(self, subscription_service):
        """Test mapping Stripe statuses to our enum."""
        mappings = [
            ("active", SubscriptionStatus.ACTIVE),
            ("trialing", SubscriptionStatus.TRIAL),
            ("past_due", SubscriptionStatus.PAST_DUE),
            ("canceled", SubscriptionStatus.CANCELED),
            ("unpaid", SubscriptionStatus.PAST_DUE),
            ("incomplete", SubscriptionStatus.INCOMPLETE),
            ("incomplete_expired", SubscriptionStatus.INCOMPLETE_EXPIRED),
            ("unknown_status", SubscriptionStatus.INCOMPLETE),  # Default
        ]

        for stripe_status, expected_status in mappings:
            result = subscription_service._map_stripe_status(stripe_status)
            assert result == expected_status
