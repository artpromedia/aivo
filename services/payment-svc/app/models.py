"""
Database models for payment service.
"""
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Numeric, Text, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .database import Base


class PlanType(str, Enum):
    """Types of subscription plans."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    """Status of subscriptions."""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"


class InvoiceStatus(str, Enum):
    """Status of invoices."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    UNCOLLECTIBLE = "uncollectible"
    VOID = "void"


class DiscountType(str, Enum):
    """Types of discounts."""
    PLAN_DURATION = "plan_duration"  # Quarterly, half-yearly, yearly discounts
    SIBLING = "sibling"  # Sibling discount
    PROMOTIONAL = "promotional"  # Promotional codes


class Subscription(Base):
    """
    Represents a subscription for a tenant or guardian.
    """
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Can be linked to either a tenant (district/school) or guardian
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    guardian_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Stripe identifiers
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Plan details
    plan_type: Mapped[PlanType] = mapped_column(SQLEnum(PlanType), nullable=False)
    seats: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # Base amount per seat
    discounted_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Status and lifecycle
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIAL
    )
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    renew_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Discount information
    discount_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="subscription", cascade="all, delete-orphan"
    )
    payment_methods: Mapped[list["PaymentMethod"]] = relationship(
        "PaymentMethod", back_populates="subscription", cascade="all, delete-orphan"
    )


class Invoice(Base):
    """
    Represents an invoice for subscription billing.
    """
    __tablename__ = "invoice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Link to subscription
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscription.id"), nullable=False, index=True
    )
    
    # Can also be directly linked to tenant/guardian for one-time payments
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    guardian_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # Stripe identifiers
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Invoice details
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    amount_subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    amount_tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    amount_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    
    # Status and URLs
    status: Mapped[InvoiceStatus] = mapped_column(SQLEnum(InvoiceStatus), nullable=False)
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invoice_pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Billing period
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Payment details
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stripe_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="invoices")


class PaymentMethod(Base):
    """
    Represents payment methods associated with subscriptions.
    """
    __tablename__ = "payment_method"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subscription.id"), nullable=False, index=True
    )
    
    # Stripe identifiers
    stripe_payment_method_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Payment method details
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # card, bank_account, etc.
    last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # visa, mastercard, etc.
    exp_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exp_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="payment_methods")


class WebhookEvent(Base):
    """
    Represents Stripe webhook events for idempotency and auditing.
    """
    __tablename__ = "webhook_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Stripe event details
    stripe_event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Processing status
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Event data
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Error handling
    processing_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DiscountRule(Base):
    """
    Represents discount rules for pricing calculations.
    """
    __tablename__ = "discount_rule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Discount details
    discount_type: Mapped[DiscountType] = mapped_column(SQLEnum(DiscountType), nullable=False)
    plan_type: Mapped[Optional[PlanType]] = mapped_column(SQLEnum(PlanType), nullable=True)
    
    # Discount amount
    percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 0-100
    fixed_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Conditions
    min_seats: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_seats: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Validity
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
