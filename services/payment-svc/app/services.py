"""
Payment service layer with Stripe integration and pricing calculations.
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import stripe
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import DiscountRule, PlanType, Subscription, SubscriptionStatus, WebhookEvent
from .schemas import (
    BASE_MONTHLY_PRICE,
    PLAN_DISCOUNTS,
    SIBLING_DISCOUNT,
    CheckoutSessionCreate,
    PricingCalculation,
    TrialStartRequest,
)

logger = logging.getLogger(__name__)


class PricingService:
    """Service for calculating subscription pricing with discounts."""

    @staticmethod
    def calculate_pricing(
        plan_type: PlanType,
        seats: int,
        has_sibling_discount: bool = False,
        additional_discounts: list[DiscountRule] | None = None,
    ) -> PricingCalculation:
        """
        Calculate subscription pricing with all applicable discounts.

        Args:
            plan_type: The subscription plan type
            seats: Number of seats
            has_sibling_discount: Whether sibling discount applies
            additional_discounts: Any additional discount rules

        Returns:
            Detailed pricing calculation
        """
        # Calculate base amount
        months = PricingService._get_plan_months(plan_type)
        base_amount = BASE_MONTHLY_PRICE * seats * months

        # Apply plan discount
        plan_discount_percentage = PLAN_DISCOUNTS.get(plan_type, Decimal("0"))
        plan_discount_amount = base_amount * plan_discount_percentage

        # Apply sibling discount
        sibling_discount_percentage = SIBLING_DISCOUNT if has_sibling_discount else Decimal("0")
        amount_after_plan_discount = base_amount - plan_discount_amount
        sibling_discount_amount = amount_after_plan_discount * sibling_discount_percentage

        # Calculate total discount
        total_discount_amount = plan_discount_amount + sibling_discount_amount
        final_amount = base_amount - total_discount_amount

        # Round to 2 decimal places
        final_amount = final_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Build discount info
        discount_info = {
            "plan_discount": {
                "type": "plan",
                "percentage": float(plan_discount_percentage * 100),
                "amount": float(plan_discount_amount),
            },
            "sibling_discount": {
                "applied": has_sibling_discount,
                "percentage": float(sibling_discount_percentage * 100),
                "amount": float(sibling_discount_amount),
            },
            "total_savings": float(total_discount_amount),
            "base_monthly_price": float(BASE_MONTHLY_PRICE),
            "billing_months": months,
        }

        return PricingCalculation(
            base_amount=base_amount,
            plan_discount_percentage=plan_discount_percentage * 100,
            plan_discount_amount=plan_discount_amount,
            sibling_discount_percentage=sibling_discount_percentage * 100,
            sibling_discount_amount=sibling_discount_amount,
            total_discount_amount=total_discount_amount,
            final_amount=final_amount,
            seats=seats,
            plan_type=plan_type,
            discount_info=discount_info,
        )

    @staticmethod
    def _get_plan_months(plan_type: PlanType) -> int:
        """Get number of months for a plan type."""
        return {
            PlanType.MONTHLY: 1,
            PlanType.QUARTERLY: 3,
            PlanType.HALF_YEARLY: 6,
            PlanType.YEARLY: 12,
        }[plan_type]


class StripeService:
    """Service for Stripe payment processing."""

    def __init__(self, api_key: str) -> None:
        """Initialize Stripe service."""
        stripe.api_key = api_key
        self.stripe = stripe

    async def create_customer(
        self,
        email: str | None = None,
        name: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Any:  # stripe.Customer
        """Create a Stripe customer."""
        customer_data = {}
        if email:
            customer_data["email"] = email
        if name:
            customer_data["name"] = name
        if metadata:
            customer_data["metadata"] = metadata

        return self.stripe.Customer.create(**customer_data)

    async def create_checkout_session(
        self,
        customer_id: str,
        line_items: list[dict[str, Any]],
        success_url: str,
        cancel_url: str,
        trial_period_days: int | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Any:  # stripe.checkout.Session
        """Create a Stripe checkout session."""
        session_data = {
            "customer": customer_id,
            "payment_method_types": ["card"],
            "line_items": line_items,
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "allow_promotion_codes": True,
            "billing_address_collection": "required",
            "customer_update": {"address": "auto", "name": "auto"},
        }

        if trial_period_days:
            session_data["subscription_data"] = {"trial_period_days": trial_period_days}

        if metadata:
            session_data["metadata"] = metadata

        return self.stripe.checkout.Session.create(**session_data)

    async def create_price(
        self,
        amount: int,  # Amount in cents
        currency: str = "usd",
        interval: str = "month",
        interval_count: int = 1,
        product_name: str = "Learning Platform Subscription",
    ) -> Any:  # stripe.Price
        """Create a Stripe price object."""
        # Create product if needed
        product = self.stripe.Product.create(name=product_name)

        return self.stripe.Price.create(
            unit_amount=amount,
            currency=currency,
            recurring={"interval": interval, "interval_count": interval_count},
            product=product.id,
        )

    async def retrieve_subscription(self, subscription_id: str) -> Any:  # stripe.Subscription
        """Retrieve a Stripe subscription."""
        return self.stripe.Subscription.retrieve(subscription_id)

    async def cancel_subscription(
        self, subscription_id: str, at_period_end: bool = True
    ) -> Any:  # stripe.Subscription
        """Cancel a Stripe subscription."""
        if at_period_end:
            return self.stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
        else:
            return self.stripe.Subscription.delete(subscription_id)

    async def retrieve_invoice(self, invoice_id: str) -> Any:  # stripe.Invoice
        """Retrieve a Stripe invoice."""
        return self.stripe.Invoice.retrieve(invoice_id)


class SubscriptionService:
    """Service for managing subscriptions."""

    def __init__(self, stripe_service: StripeService) -> None:
        """Initialize subscription service."""
        self.stripe_service = stripe_service
        self.pricing_service = PricingService()

    async def start_trial(self, db: AsyncSession, request: TrialStartRequest) -> Subscription:
        """Start a trial subscription."""
        # Calculate pricing for monthly plan (trial defaults to monthly)
        pricing = self.pricing_service.calculate_pricing(
            plan_type=PlanType.MONTHLY, seats=request.seats, has_sibling_discount=False
        )

        # Create subscription record
        trial_start = datetime.now(UTC)
        trial_end = trial_start + timedelta(days=14)  # 14-day trial

        subscription = Subscription(
            tenant_id=request.tenant_id,
            guardian_id=request.guardian_id,
            plan_type=PlanType.MONTHLY,
            seats=request.seats,
            base_amount=pricing.base_amount,
            discounted_amount=pricing.final_amount,
            status=SubscriptionStatus.TRIAL,
            trial_start=trial_start,
            trial_end=trial_end,
            discount_info=pricing.discount_info,
        )

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        logger.info(f"Started trial subscription {subscription.id}")
        return subscription

    async def create_checkout_session(
        self, db: AsyncSession, request: CheckoutSessionCreate
    ) -> tuple[str, str, int | None]:
        """Create a Stripe checkout session for subscription."""
        # Calculate pricing
        pricing = self.pricing_service.calculate_pricing(
            plan_type=request.plan_type,
            seats=request.seats,
            has_sibling_discount=request.has_sibling_discount,
        )

        # Create or get Stripe customer
        customer_metadata = {}
        if request.tenant_id:
            customer_metadata["tenant_id"] = str(request.tenant_id)
        if request.guardian_id:
            customer_metadata["guardian_id"] = request.guardian_id

        customer = await self.stripe_service.create_customer(metadata=customer_metadata)

        # Create price object for this specific configuration
        amount_in_cents = int(pricing.final_amount * 100)
        months = self.pricing_service._get_plan_months(request.plan_type)

        price = await self.stripe_service.create_price(
            amount=amount_in_cents,
            interval="month",
            interval_count=months,
            product_name=f"Learning Platform - {request.seats} seats - {request.plan_type.value}",
        )

        # Create checkout session
        line_items = [{"price": price.id, "quantity": 1}]

        session_metadata = {
            "plan_type": request.plan_type.value,
            "seats": str(request.seats),
            "has_sibling_discount": str(request.has_sibling_discount),
            "base_amount": str(pricing.base_amount),
            "final_amount": str(pricing.final_amount),
        }
        session_metadata.update(customer_metadata)

        session = await self.stripe_service.create_checkout_session(
            customer_id=customer.id,
            line_items=line_items,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata=session_metadata,
        )

        # Create pending subscription record
        subscription = Subscription(
            tenant_id=request.tenant_id,
            guardian_id=request.guardian_id,
            plan_type=request.plan_type,
            seats=request.seats,
            base_amount=pricing.base_amount,
            discounted_amount=pricing.final_amount,
            stripe_customer_id=customer.id,
            status=SubscriptionStatus.INCOMPLETE,
            discount_info=pricing.discount_info,
        )

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        logger.info(f"Created checkout session {session.id} for subscription {subscription.id}")
        return session.id, session.url, subscription.id

    async def get_subscription_by_id(
        self, db: AsyncSession, subscription_id: int
    ) -> Subscription | None:
        """Get subscription by ID."""
        result = await db.execute(select(Subscription).where(Subscription.id == subscription_id))
        return result.scalar_one_or_none()

    async def get_subscriptions_by_tenant(
        self, db: AsyncSession, tenant_id: int
    ) -> list[Subscription]:
        """Get all subscriptions for a tenant."""
        result = await db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
        return result.scalars().all()

    async def get_subscriptions_by_guardian(
        self, db: AsyncSession, guardian_id: str
    ) -> list[Subscription]:
        """Get all subscriptions for a guardian."""
        result = await db.execute(
            select(Subscription).where(Subscription.guardian_id == guardian_id)
        )
        return result.scalars().all()

    async def update_subscription_from_stripe(
        self, db: AsyncSession, subscription_id: int, stripe_subscription: Any
    ) -> Subscription:
        """Update subscription from Stripe webhook data."""
        subscription = await self.get_subscription_by_id(db, subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        # Update from Stripe data
        subscription.stripe_subscription_id = stripe_subscription.id
        subscription.status = self._map_stripe_status(stripe_subscription.status)
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_subscription.current_period_start, tz=UTC
        )
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription.current_period_end, tz=UTC
        )

        if stripe_subscription.trial_start:
            subscription.trial_start = datetime.fromtimestamp(stripe_subscription.trial_start)
        if stripe_subscription.trial_end:
            subscription.trial_end = datetime.fromtimestamp(stripe_subscription.trial_end)

        if stripe_subscription.canceled_at:
            subscription.canceled_at = datetime.fromtimestamp(stripe_subscription.canceled_at)

        await db.commit()
        await db.refresh(subscription)

        logger.info(f"Updated subscription {subscription_id} from Stripe")
        return subscription

    def _map_stripe_status(self, stripe_status: str) -> SubscriptionStatus:
        """Map Stripe subscription status to our enum."""
        mapping = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIAL,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "unpaid": SubscriptionStatus.PAST_DUE,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        }
        return mapping.get(stripe_status, SubscriptionStatus.INCOMPLETE)


class WebhookService:
    """Service for processing Stripe webhooks."""

    def __init__(self, subscription_service: SubscriptionService) -> None:
        """Initialize webhook service."""
        self.subscription_service = subscription_service

    async def process_webhook(
        self, db: AsyncSession, event_id: str, event_type: str, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process a Stripe webhook event."""
        # Check if we've already processed this event
        existing_event = await self._get_webhook_event(db, event_id)
        if existing_event:
            logger.info(f"Webhook event {event_id} already processed")
            return {"processed": True, "message": "Event already processed"}

        # Record the webhook event
        webhook_event = WebhookEvent(
            stripe_event_id=event_id, event_type=event_type, event_data=event_data, processed=False
        )
        db.add(webhook_event)

        try:
            result = await self._handle_webhook_event(db, event_type, event_data)
            webhook_event.processed = True
            webhook_event.processed_at = datetime.now(UTC)
            await db.commit()

            logger.info(f"Processed webhook event {event_id}: {event_type}")
            return result

        except Exception as e:
            logger.error(f"Error processing webhook {event_id}: {str(e)}")
            webhook_event.error_message = str(e)
            await db.commit()
            raise

    async def _handle_webhook_event(
        self, db: AsyncSession, event_type: str, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle specific webhook event types."""
        if event_type == "checkout.session.completed":
            return await self._handle_checkout_completed(db, event_data)
        elif event_type == "customer.subscription.updated":
            return await self._handle_subscription_updated(db, event_data)
        elif event_type == "customer.subscription.deleted":
            return await self._handle_subscription_deleted(db, event_data)
        elif event_type == "invoice.payment_succeeded":
            return await self._handle_invoice_payment_succeeded(db, event_data)
        elif event_type == "invoice.payment_failed":
            return await self._handle_invoice_payment_failed(db, event_data)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return {"processed": True, "message": f"Event type {event_type} not handled"}

    async def _handle_checkout_completed(
        self, db: AsyncSession, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle checkout session completed."""
        session = event_data["object"]
        session.get("metadata", {})

        # Find the subscription by metadata
        subscription_query = select(Subscription).where(
            and_(
                Subscription.stripe_customer_id == session["customer"],
                Subscription.status == SubscriptionStatus.INCOMPLETE,
            )
        )

        result = await db.execute(subscription_query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            logger.warning(f"No pending subscription found for customer {session['customer']}")
            return {"processed": False, "message": "Subscription not found"}

        # Update subscription with Stripe data
        subscription.stripe_subscription_id = session["subscription"]
        subscription.status = SubscriptionStatus.ACTIVE

        await db.commit()

        return {
            "processed": True,
            "message": "Checkout completed",
            "subscription_id": subscription.id,
        }

    async def _handle_subscription_updated(
        self, db: AsyncSession, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle subscription updated."""
        stripe_subscription = event_data["object"]

        # Find our subscription record
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription["id"]
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            logger.warning(f"Subscription not found for Stripe ID {stripe_subscription['id']}")
            return {"processed": False, "message": "Subscription not found"}

        # Update subscription
        await self.subscription_service.update_subscription_from_stripe(
            db, subscription.id, stripe_subscription
        )

        return {
            "processed": True,
            "message": "Subscription updated",
            "subscription_id": subscription.id,
        }

    async def _handle_subscription_deleted(
        self, db: AsyncSession, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle subscription deleted."""
        stripe_subscription = event_data["object"]

        # Find our subscription record
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_subscription["id"]
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            logger.warning(f"Subscription not found for Stripe ID {stripe_subscription['id']}")
            return {"processed": False, "message": "Subscription not found"}

        # Mark as canceled
        subscription.status = SubscriptionStatus.CANCELED
        subscription.canceled_at = datetime.now(UTC)

        await db.commit()

        return {
            "processed": True,
            "message": "Subscription canceled",
            "subscription_id": subscription.id,
        }

    async def _handle_invoice_payment_succeeded(
        self, db: AsyncSession, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle successful invoice payment."""
        stripe_invoice = event_data["object"]

        # TODO: Create/update invoice record
        # This would involve creating an Invoice model instance
        # and updating the subscription status if needed

        return {
            "processed": True,
            "message": "Invoice payment succeeded",
            "invoice_id": stripe_invoice["id"],
        }

    async def _handle_invoice_payment_failed(
        self, db: AsyncSession, event_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle failed invoice payment."""
        stripe_invoice = event_data["object"]

        # TODO: Handle payment failure
        # This might involve updating subscription status,
        # sending notifications, etc.

        return {
            "processed": True,
            "message": "Invoice payment failed",
            "invoice_id": stripe_invoice["id"],
        }

    async def _get_webhook_event(self, db: AsyncSession, event_id: str) -> WebhookEvent | None:
        """Get webhook event by Stripe event ID."""
        result = await db.execute(
            select(WebhookEvent).where(WebhookEvent.stripe_event_id == event_id)
        )
        return result.scalar_one_or_none()
