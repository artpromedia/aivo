"""
Pydantic schemas for payment service.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, validator, model_validator

from .models import PlanType, SubscriptionStatus, InvoiceStatus, DiscountType


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
    tenant_id: Optional[int] = None
    guardian_id: Optional[str] = None
    plan_type: PlanType
    seats: int = Field(..., gt=0, le=1000)
    success_url: str = Field(..., min_length=1)
    cancel_url: str = Field(..., min_length=1)
    has_sibling_discount: bool = False
    promotional_code: Optional[str] = None

    @model_validator(mode='after')
    def validate_tenant_or_guardian(self):
        """Ensure either tenant_id or guardian_id is provided."""
        if not self.tenant_id and not self.guardian_id:
            raise ValueError('Either tenant_id or guardian_id must be provided')
        if self.tenant_id and self.guardian_id:
            raise ValueError('Cannot specify both tenant_id and guardian_id')
        return self


class CheckoutSessionResponse(BaseModel):
    """Response for checkout session creation."""
    session_id: str
    session_url: str
    subscription_id: Optional[int] = None


# Trial schemas
class TrialStartRequest(BaseModel):
    """Schema for starting a trial."""
    tenant_id: Optional[int] = None
    guardian_id: Optional[str] = None
    seats: int = Field(..., gt=0, le=1000)

    @model_validator(mode='after')
    def validate_tenant_or_guardian(self):
        """Ensure either tenant_id or guardian_id is provided."""
        if not self.tenant_id and not self.guardian_id:
            raise ValueError('Either tenant_id or guardian_id must be provided')
        if self.tenant_id and self.guardian_id:
            raise ValueError('Cannot specify both tenant_id and guardian_id')
        return self


# Subscription schemas
class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    tenant_id: Optional[int] = None
    guardian_id: Optional[str] = None
    plan_type: PlanType
    seats: int
    base_amount: Decimal
    discounted_amount: Optional[Decimal] = None


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating subscriptions."""
    stripe_customer_id: Optional[str] = None
    has_sibling_discount: bool = False


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscriptions."""
    seats: Optional[int] = Field(None, gt=0, le=1000)
    status: Optional[SubscriptionStatus] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None


class Subscription(SubscriptionBase):
    """Full subscription schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    status: SubscriptionStatus
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    renew_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    discount_info: Optional[Dict[str, Any]] = None
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
    tenant_id: Optional[int] = None
    guardian_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    description: Optional[str] = None


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""
    status: Optional[InvoiceStatus] = None
    amount_paid: Optional[Decimal] = None
    amount_due: Optional[Decimal] = None
    paid_at: Optional[datetime] = None
    hosted_invoice_url: Optional[str] = None
    invoice_pdf_url: Optional[str] = None


class Invoice(InvoiceBase):
    """Full invoice schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    tenant_id: Optional[int] = None
    guardian_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    invoice_number: Optional[str] = None
    amount_paid: Decimal
    amount_due: Decimal
    hosted_invoice_url: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    description: Optional[str] = None
    stripe_metadata: Optional[Dict[str, Any]] = None
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
    discount_info: Dict[str, Any]


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
    data: Dict[str, Any]
    created: int
    livemode: bool


class WebhookEventResponse(BaseModel):
    """Response for webhook processing."""
    processed: bool
    message: str
    subscription_id: Optional[int] = None
    invoice_id: Optional[int] = None


# Discount schemas
class DiscountRuleBase(BaseModel):
    """Base discount rule schema."""
    discount_type: DiscountType
    plan_type: Optional[PlanType] = None
    percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    fixed_amount: Optional[Decimal] = Field(None, ge=0)
    name: str
    description: Optional[str] = None


class DiscountRuleCreate(DiscountRuleBase):
    """Schema for creating discount rules."""
    min_seats: Optional[int] = Field(None, gt=0)
    max_seats: Optional[int] = Field(None, gt=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class DiscountRule(DiscountRuleBase):
    """Full discount rule schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    min_seats: Optional[int] = None
    max_seats: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Payment method schemas
class PaymentMethodBase(BaseModel):
    """Base payment method schema."""
    type: str
    last4: Optional[str] = None
    brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None


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
    error_code: Optional[str] = None
    stripe_error: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    data: Optional[Dict[str, Any]] = None


# Summary schemas
class SubscriptionSummary(BaseModel):
    """Summary of subscription details."""
    subscription: Subscription
    latest_invoice: Optional[Invoice] = None
    payment_methods: List[PaymentMethod] = []
    total_paid: Decimal
    next_billing_date: Optional[datetime] = None


class PaymentAnalytics(BaseModel):
    """Payment analytics schema."""
    total_subscriptions: int
    active_subscriptions: int
    trial_subscriptions: int
    total_revenue: Decimal
    monthly_recurring_revenue: Decimal
    average_revenue_per_user: Decimal
    churn_rate: Optional[Decimal] = None
