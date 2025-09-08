"""
Pydantic schemas for payment service.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import DiscountType, InvoiceStatus, PlanType, SubscriptionStatus

# Base pricing configuration
BASE_MONTHLY_PRICE = Decimal("40.00")

# Discount configurations
PLAN_DISCOUNTS = {
    PlanType.QUARTERLY: Decimal("0.20"),  # 20% off
    PlanType.HALF_YEARLY: Decimal("0.30"),  # 30% off
    PlanType.YEARLY: Decimal("0.50"),  # 50% off
}

SIBLING_DISCOUNT = Decimal("0.10")  # 10% off


# Checkout schemas
class CheckoutSessionCreate(BaseModel):
    """Schema for creating a checkout session."""

    tenant_id: int | None = None
    guardian_id: str | None = None
    plan_type: PlanType
    seats: int = Field(..., gt=0, le=1000)
    success_url: str = Field(..., min_length=1)
    cancel_url: str = Field(..., min_length=1)
    has_sibling_discount: bool = False
    promotional_code: str | None = None

    @model_validator(mode="after")
    def validate_tenant_or_guardian(self):
        """Ensure either tenant_id or guardian_id is provided."""
        if not self.tenant_id and not self.guardian_id:
            raise ValueError("Either tenant_id or guardian_id must be provided")
        if self.tenant_id and self.guardian_id:
            raise ValueError("Cannot specify both tenant_id and guardian_id")
        return self


class CheckoutSessionResponse(BaseModel):
    """Response for checkout session creation."""

    session_id: str
    session_url: str
    subscription_id: int | None = None


# Trial schemas
class TrialStartRequest(BaseModel):
    """Schema for starting a trial."""

    tenant_id: int | None = None
    guardian_id: str | None = None
    seats: int = Field(..., gt=0, le=1000)

    @model_validator(mode="after")
    def validate_tenant_or_guardian(self):
        """Ensure either tenant_id or guardian_id is provided."""
        if not self.tenant_id and not self.guardian_id:
            raise ValueError("Either tenant_id or guardian_id must be provided")
        if self.tenant_id and self.guardian_id:
            raise ValueError("Cannot specify both tenant_id and guardian_id")
        return self


# Subscription schemas
class SubscriptionBase(BaseModel):
    """Base subscription schema."""

    tenant_id: int | None = None
    guardian_id: str | None = None
    plan_type: PlanType
    seats: int
    base_amount: Decimal
    discounted_amount: Decimal | None = None


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating subscriptions."""

    stripe_customer_id: str | None = None
    has_sibling_discount: bool = False


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscriptions."""

    seats: int | None = Field(None, gt=0, le=1000)
    status: SubscriptionStatus | None = None
    stripe_subscription_id: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    canceled_at: datetime | None = None


class Subscription(SubscriptionBase):
    """Full subscription schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None
    status: SubscriptionStatus
    trial_start: datetime | None = None
    trial_end: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    renew_at: datetime | None = None
    canceled_at: datetime | None = None
    discount_info: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    is_active: bool


# Invoice schemas
class InvoiceBase(BaseModel):
    """Base invoice schema."""

    subscription_id: int
    amount_subtotal: Decimal
    amount_discount: Decimal = Decimal("0")
    amount_tax: Decimal = Decimal("0")
    amount_total: Decimal
    status: InvoiceStatus


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""

    tenant_id: int | None = None
    guardian_id: str | None = None
    stripe_invoice_id: str | None = None
    description: str | None = None


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""

    status: InvoiceStatus | None = None
    amount_paid: Decimal | None = None
    amount_due: Decimal | None = None
    paid_at: datetime | None = None
    hosted_invoice_url: str | None = None
    invoice_pdf_url: str | None = None


class Invoice(InvoiceBase):
    """Full invoice schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int | None = None
    guardian_id: str | None = None
    stripe_invoice_id: str | None = None
    stripe_payment_intent_id: str | None = None
    invoice_number: str | None = None
    amount_paid: Decimal
    amount_due: Decimal
    hosted_invoice_url: str | None = None
    invoice_pdf_url: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    due_date: datetime | None = None
    paid_at: datetime | None = None
    description: str | None = None
    stripe_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


# Pricing schemas
class PricingCalculation(BaseModel):
    """Schema for pricing calculations."""

    base_amount: Decimal
    plan_discount_percentage: Decimal = Decimal("0")
    plan_discount_amount: Decimal = Decimal("0")
    sibling_discount_percentage: Decimal = Decimal("0")
    sibling_discount_amount: Decimal = Decimal("0")
    total_discount_amount: Decimal = Decimal("0")
    final_amount: Decimal
    seats: int
    plan_type: PlanType
    discount_info: dict[str, Any]


class PricingRequest(BaseModel):
    """Schema for pricing calculation requests."""

    plan_type: PlanType
    seats: int = Field(..., gt=0, le=1000)
    has_sibling_discount: bool = False


# Webhook schemas
class StripeWebhookEvent(BaseModel):
    """Schema for Stripe webhook events."""

    id: str
    type: str
    data: dict[str, Any]
    created: int
    livemode: bool


class WebhookEventResponse(BaseModel):
    """Response for webhook processing."""

    processed: bool
    message: str
    subscription_id: int | None = None
    invoice_id: int | None = None


# Discount schemas
class DiscountRuleBase(BaseModel):
    """Base discount rule schema."""

    discount_type: DiscountType
    plan_type: PlanType | None = None
    percentage: Decimal | None = Field(None, ge=0, le=100)
    fixed_amount: Decimal | None = Field(None, ge=0)
    name: str
    description: str | None = None


class DiscountRuleCreate(DiscountRuleBase):
    """Schema for creating discount rules."""

    min_seats: int | None = Field(None, gt=0)
    max_seats: int | None = Field(None, gt=0)
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class DiscountRule(DiscountRuleBase):
    """Full discount rule schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    min_seats: int | None = None
    max_seats: int | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Payment method schemas
class PaymentMethodBase(BaseModel):
    """Base payment method schema."""

    type: str
    last4: str | None = None
    brand: str | None = None
    exp_month: int | None = None
    exp_year: int | None = None


class PaymentMethod(PaymentMethodBase):
    """Full payment method schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    stripe_payment_method_id: str
    stripe_customer_id: str
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Response schemas
class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    error_code: str | None = None
    stripe_error: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    data: dict[str, Any] | None = None


# Summary schemas
class SubscriptionSummary(BaseModel):
    """Summary of subscription details."""

    subscription: Subscription
    latest_invoice: Invoice | None = None
    payment_methods: list[PaymentMethod] = []
    total_paid: Decimal
    next_billing_date: datetime | None = None


class PaymentAnalytics(BaseModel):
    """Payment analytics schema."""

    total_subscriptions: int
    active_subscriptions: int
    trial_subscriptions: int
    total_revenue: Decimal
    monthly_recurring_revenue: Decimal
    average_revenue_per_user: Decimal
    churn_rate: Decimal | None = None
