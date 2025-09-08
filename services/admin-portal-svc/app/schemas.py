"""
Pydantic schemas for the Admin Portal Aggregator Service.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    """Tenant status enum."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CANCELLED = "cancelled"


class SubscriptionTier(str, Enum):
    """Subscription tier enum."""

    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class UsageMetric(BaseModel):
    """Usage metric model."""

    metric_name: str = Field(..., description="Name of the metric")
    current_value: int = Field(..., description="Current usage value")
    limit_value: int | None = Field(None, description="Usage limit")
    percentage_used: float = Field(..., description="Percentage of limit used")
    unit: str = Field(..., description="Unit of measurement")


class SummaryResponse(BaseModel):
    """Summary dashboard response."""

    tenant_id: str = Field(..., description="Tenant identifier")
    tenant_name: str = Field(..., description="Tenant display name")
    status: TenantStatus = Field(..., description="Current tenant status")
    subscription_tier: SubscriptionTier = Field(..., description="Current subscription tier")
    total_users: int = Field(..., description="Total number of users")
    active_users_30d: int = Field(..., description="Active users in last 30 days")
    total_documents: int = Field(..., description="Total documents processed")
    pending_approvals: int = Field(..., description="Number of pending approvals")
    monthly_spend: Decimal = Field(..., description="Current month spending")
    usage_alerts: int = Field(default=0, description="Number of usage alerts")
    last_activity: datetime | None = Field(None, description="Last activity timestamp")
    health_score: float = Field(..., ge=0, le=100, description="Overall health score")


class SubscriptionDetails(BaseModel):
    """Subscription details response."""

    tenant_id: str = Field(..., description="Tenant identifier")
    current_tier: SubscriptionTier = Field(..., description="Current subscription tier")
    billing_cycle: str = Field(..., description="Billing cycle (monthly/yearly)")
    next_billing_date: datetime = Field(..., description="Next billing date")
    monthly_cost: Decimal = Field(..., description="Monthly subscription cost")
    yearly_cost: Decimal | None = Field(None, description="Yearly subscription cost")
    features: list[str] = Field(..., description="Available features")
    usage_limits: dict[str, int] = Field(..., description="Usage limits by resource")
    auto_renewal: bool = Field(..., description="Auto-renewal status")
    trial_end_date: datetime | None = Field(None, description="Trial end date if applicable")
    discount_applied: str | None = Field(None, description="Applied discount details")


class BillingHistoryItem(BaseModel):
    """Billing history item."""

    invoice_id: str = Field(..., description="Invoice identifier")
    date: datetime = Field(..., description="Invoice date")
    amount: Decimal = Field(..., description="Invoice amount")
    status: str = Field(..., description="Payment status")
    description: str = Field(..., description="Invoice description")
    download_url: str | None = Field(None, description="PDF download URL")


class BillingHistoryResponse(BaseModel):
    """Billing history response."""

    tenant_id: str = Field(..., description="Tenant identifier")
    current_balance: Decimal = Field(..., description="Current account balance")
    next_payment_due: datetime | None = Field(None, description="Next payment due date")
    payment_method: str | None = Field(None, description="Default payment method")
    invoices: list[BillingHistoryItem] = Field(..., description="Invoice history")
    total_spent_ytd: Decimal = Field(..., description="Total spent year-to-date")


class TeamMember(BaseModel):
    """Team member details."""

    user_id: str = Field(..., description="User identifier")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    status: str = Field(..., description="User status")
    last_login: datetime | None = Field(None, description="Last login timestamp")
    permissions: list[str] = Field(..., description="User permissions")
    invite_status: str | None = Field(None, description="Invite status if pending")


class TeamResponse(BaseModel):
    """Team dashboard response."""

    tenant_id: str = Field(..., description="Tenant identifier")
    total_members: int = Field(..., description="Total team members")
    active_members: int = Field(..., description="Active team members")
    pending_invites: int = Field(..., description="Pending invitations")
    members: list[TeamMember] = Field(..., description="Team member details")
    role_distribution: dict[str, int] = Field(..., description="Distribution by role")
    recent_activity: list[dict[str, Any]] = Field(..., description="Recent team activity")


class UsageResponse(BaseModel):
    """Usage dashboard response."""

    tenant_id: str = Field(..., description="Tenant identifier")
    billing_period_start: datetime = Field(..., description="Current billing period start")
    billing_period_end: datetime = Field(..., description="Current billing period end")
    metrics: list[UsageMetric] = Field(..., description="Usage metrics")
    total_api_calls: int = Field(..., description="Total API calls this period")
    total_storage_gb: float = Field(..., description="Total storage used in GB")
    bandwidth_gb: float = Field(..., description="Bandwidth used in GB")
    cost_breakdown: dict[str, Decimal] = Field(..., description="Cost breakdown by service")
    projected_monthly_cost: Decimal = Field(..., description="Projected monthly cost")
    usage_trends: dict[str, list[float]] = Field(..., description="Usage trends over time")


class NamespaceInfo(BaseModel):
    """Information about a namespace."""

    model_config = {"protected_namespaces": ()}

    namespace_id: str
    name: str
    status: str
    document_count: int
    storage_used_mb: float
    last_updated: datetime
    model_deployments: int
    active_workflows: int


class NamespacesResponse(BaseModel):
    """Namespaces dashboard response."""

    tenant_id: str = Field(..., description="Tenant identifier")
    total_namespaces: int = Field(..., description="Total number of namespaces")
    active_namespaces: int = Field(..., description="Active namespaces")
    total_documents: int = Field(..., description="Total documents across namespaces")
    total_storage_gb: float = Field(..., description="Total storage used in GB")
    namespaces: list[NamespaceInfo] = Field(..., description="Namespace details")
    storage_distribution: dict[str, float] = Field(
        ..., description="Storage distribution by namespace"
    )


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    dependencies: dict[str, str] = Field(..., description="Dependency status")
    cache_status: str = Field(..., description="Cache status")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    request_id: str | None = Field(None, description="Request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
