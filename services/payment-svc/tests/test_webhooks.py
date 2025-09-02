"""
Tests for webhook service functionality.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from app.models import SubscriptionStatus
from app.schemas import TrialStartRequest


class TestWebhookService:
    """Test webhook processing."""
    
    @pytest.mark.asyncio
    async def test_process_new_webhook(self, webhook_service, db_session):
        """Test processing a new webhook event."""
        # Create a subscription in INCOMPLETE status to be updated by the webhook
        from app.models import Subscription, PlanType
        subscription = Subscription(
            tenant_id=1,
            plan_type=PlanType.MONTHLY,
            seats=5,
            base_amount=200,
            stripe_customer_id="cus_test123",
            status=SubscriptionStatus.INCOMPLETE
        )
        db_session.add(subscription)
        await db_session.commit()
        
        event_data = {
            "object": {
                "id": "cs_test123",
                "customer": "cus_test123",
                "subscription": "sub_test123"
            }
        }
        
        result = await webhook_service.process_webhook(
            db_session,
            "evt_test123",
            "checkout.session.completed",
            event_data
        )
        
        assert result["processed"] is True
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_process_duplicate_webhook(self, webhook_service, db_session):
        """Test processing the same webhook event twice."""
        event_data = {
            "object": {
                "id": "cs_test123",
                "customer": "cus_test123",
                "subscription": "sub_test123"
            }
        }
        
        # Process first time
        await webhook_service.process_webhook(
            db_session,
            "evt_test123",
            "checkout.session.completed",
            event_data
        )
        
        # Process second time (should be idempotent)
        result = await webhook_service.process_webhook(
            db_session,
            "evt_test123",
            "checkout.session.completed",
            event_data
        )
        
        assert result["processed"] is True
        assert result["message"] == "Event already processed"
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed(self, webhook_service, subscription_service, db_session):
        """Test handling checkout session completed webhook."""
        # First create a pending subscription
        from app.schemas import CheckoutSessionCreate
        checkout_request = CheckoutSessionCreate(
            tenant_id=1,
            plan_type="monthly",
            seats=5,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        # Mock the checkout session creation to create a pending subscription
        from app.models import Subscription, PlanType
        subscription = Subscription(
            tenant_id=1,
            plan_type=PlanType.MONTHLY,
            seats=5,
            base_amount=200,
            stripe_customer_id="cus_test123",
            status=SubscriptionStatus.INCOMPLETE
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        
        # Now process the webhook
        event_data = {
            "object": {
                "id": "cs_test123",
                "customer": "cus_test123",
                "subscription": "sub_test123",
                "metadata": {
                    "tenant_id": "1",
                    "plan_type": "monthly",
                    "seats": "5"
                }
            }
        }
        
        result = await webhook_service._handle_checkout_completed(db_session, event_data)
        
        assert result["processed"] is True
        assert result["message"] == "Checkout completed"
        assert "subscription_id" in result
        
        # Check that subscription was updated
        await db_session.refresh(subscription)
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.stripe_subscription_id == "sub_test123"
    
    @pytest.mark.asyncio
    async def test_handle_subscription_updated(self, webhook_service, subscription_service, db_session):
        """Test handling subscription updated webhook."""
        # Create a subscription with Stripe ID
        from app.models import Subscription, PlanType
        subscription = Subscription(
            tenant_id=1,
            plan_type=PlanType.MONTHLY,
            seats=5,
            base_amount=200,
            stripe_subscription_id="sub_test123",
            status=SubscriptionStatus.ACTIVE
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        
        # Mock updated Stripe subscription data
        stripe_subscription_data = {
            "id": "sub_test123",
            "status": "past_due",
            "current_period_start": 1640995200,
            "current_period_end": 1643673600,
            "trial_start": None,
            "trial_end": None,
            "canceled_at": None
        }
        
        event_data = {"object": stripe_subscription_data}
        
        # Mock the subscription service method
        subscription_service.update_subscription_from_stripe = AsyncMock()
        subscription_service.update_subscription_from_stripe.return_value = subscription
        
        result = await webhook_service._handle_subscription_updated(db_session, event_data)
        
        assert result["processed"] is True
        assert result["message"] == "Subscription updated"
        assert result["subscription_id"] == subscription.id
    
    @pytest.mark.asyncio
    async def test_handle_subscription_deleted(self, webhook_service, db_session):
        """Test handling subscription deleted webhook."""
        # Create a subscription
        from app.models import Subscription, PlanType
        subscription = Subscription(
            tenant_id=1,
            plan_type=PlanType.MONTHLY,
            seats=5,
            base_amount=200,
            stripe_subscription_id="sub_test123",
            status=SubscriptionStatus.ACTIVE
        )
        db_session.add(subscription)
        await db_session.commit()
        await db_session.refresh(subscription)
        
        # Process deletion webhook
        event_data = {
            "object": {
                "id": "sub_test123"
            }
        }
        
        result = await webhook_service._handle_subscription_deleted(db_session, event_data)
        
        assert result["processed"] is True
        assert result["message"] == "Subscription canceled"
        assert result["subscription_id"] == subscription.id
        
        # Check that subscription was marked as canceled
        await db_session.refresh(subscription)
        assert subscription.status == SubscriptionStatus.CANCELED
        assert subscription.canceled_at is not None
    
    @pytest.mark.asyncio
    async def test_handle_invoice_payment_succeeded(self, webhook_service, db_session):
        """Test handling invoice payment succeeded webhook."""
        event_data = {
            "object": {
                "id": "in_test123",
                "subscription": "sub_test123",
                "amount_paid": 4000,
                "status": "paid"
            }
        }
        
        result = await webhook_service._handle_invoice_payment_succeeded(db_session, event_data)
        
        assert result["processed"] is True
        assert result["message"] == "Invoice payment succeeded"
        assert result["invoice_id"] == "in_test123"
    
    @pytest.mark.asyncio
    async def test_handle_invoice_payment_failed(self, webhook_service, db_session):
        """Test handling invoice payment failed webhook."""
        event_data = {
            "object": {
                "id": "in_test123",
                "subscription": "sub_test123",
                "amount_due": 4000,
                "status": "open"
            }
        }
        
        result = await webhook_service._handle_invoice_payment_failed(db_session, event_data)
        
        assert result["processed"] is True
        assert result["message"] == "Invoice payment failed"
        assert result["invoice_id"] == "in_test123"
    
    @pytest.mark.asyncio
    async def test_handle_unknown_event_type(self, webhook_service, db_session):
        """Test handling unknown webhook event type."""
        event_data = {"object": {"id": "test123"}}
        
        result = await webhook_service._handle_webhook_event(
            db_session,
            "unknown.event.type",
            event_data
        )
        
        assert result["processed"] is True
        assert "not handled" in result["message"]
