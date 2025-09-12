"""
Tenant model for multi-tenancy support.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any

from sqlalchemy import Boolean, JSON, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class TenantStatus(str, Enum):
    """Tenant status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class TenantPlan(str, Enum):
    """Tenant subscription plans."""

    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class Tenant(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Tenant model for multi-tenancy support.

    Manages tenant-specific configurations, billing, and isolation
    for SSO services in a multi-tenant environment.
    """

    __tablename__ = "tenants"

    # Basic tenant information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tenant identification
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)

    # Tenant status and plan
    status: Mapped[TenantStatus] = mapped_column(
        SQLEnum(TenantStatus),
        nullable=False,
        default=TenantStatus.PENDING,
        index=True
    )
    plan: Mapped[TenantPlan] = mapped_column(
        SQLEnum(TenantPlan),
        nullable=False,
        default=TenantPlan.BASIC
    )

    # Contact information
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Domain and URL configuration
    primary_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allowed_domains: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    custom_logo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    custom_css_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Feature flags and limits
    features_enabled: Mapped[Dict[str, bool]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "saml_sso": True,
            "oauth_sso": False,
            "scim_provisioning": False,
            "audit_logs": True,
            "custom_branding": False,
            "advanced_mappings": False,
            "multi_provider": False,
            "api_access": True
        }
    )

    # Usage limits
    limits: Mapped[Dict[str, int]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "max_users": 100,
            "max_providers": 1,
            "max_sessions": 500,
            "api_calls_per_hour": 1000,
            "audit_retention_days": 30
        }
    )

    # Current usage statistics
    usage_stats: Mapped[Dict[str, int]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "active_users": 0,
            "active_providers": 0,
            "active_sessions": 0,
            "api_calls_today": 0,
            "storage_used_mb": 0
        }
    )

    # Billing information
    billing_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billing_address: Mapped[Dict[str, str] | None] = mapped_column(JSON, nullable=True)
    payment_method_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Subscription details
    subscription_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Security settings
    security_settings: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "enforce_mfa": False,
            "session_timeout_minutes": 60,
            "max_concurrent_sessions": 5,
            "ip_whitelist": [],
            "require_ssl": True,
            "audit_all_events": True
        }
    )

    # Integration settings
    integrations: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {}
    )

    # Metadata and custom fields
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {}
    )

    # Activity tracking
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', status='{self.status}')>"

    def is_active(self) -> bool:
        """Check if tenant is active and not deleted."""
        return self.status == TenantStatus.ACTIVE and not self.is_deleted

    def is_trial(self) -> bool:
        """Check if tenant is in trial period."""
        return (
            self.trial_end is not None and
            datetime.utcnow() < self.trial_end
        )

    def is_subscription_active(self) -> bool:
        """Check if tenant has active subscription."""
        if self.subscription_end is None:
            return False
        return datetime.utcnow() < self.subscription_end

    def has_feature(self, feature: str) -> bool:
        """Check if tenant has access to a specific feature."""
        return self.features_enabled.get(feature, False)

    def get_limit(self, limit_name: str) -> int | None:
        """Get usage limit for a specific resource."""
        return self.limits.get(limit_name)

    def get_usage(self, stat_name: str) -> int:
        """Get current usage for a specific statistic."""
        return self.usage_stats.get(stat_name, 0)

    def is_limit_exceeded(self, limit_name: str, current_usage: int | None = None) -> bool:
        """Check if usage limit is exceeded."""
        limit = self.get_limit(limit_name)
        if limit is None:
            return False

        if current_usage is None:
            # Try to get current usage from stats
            usage_stat_map = {
                "max_users": "active_users",
                "max_providers": "active_providers",
                "max_sessions": "active_sessions"
            }
            stat_name = usage_stat_map.get(limit_name)
            if stat_name:
                current_usage = self.get_usage(stat_name)
            else:
                return False

        return current_usage >= limit

    def update_usage_stat(self, stat_name: str, value: int) -> None:
        """Update usage statistic."""
        if self.usage_stats is None:
            self.usage_stats = {}
        self.usage_stats[stat_name] = value

    def increment_usage_stat(self, stat_name: str, increment: int = 1) -> None:
        """Increment usage statistic."""
        if self.usage_stats is None:
            self.usage_stats = {}
        current = self.usage_stats.get(stat_name, 0)
        self.usage_stats[stat_name] = current + increment

    def get_security_setting(self, setting: str, default: Any = None) -> Any:
        """Get security setting value."""
        if self.security_settings is None:
            return default
        return self.security_settings.get(setting, default)

    def set_security_setting(self, setting: str, value: Any) -> None:
        """Set security setting value."""
        if self.security_settings is None:
            self.security_settings = {}
        self.security_settings[setting] = value

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is allowed for this tenant."""
        if not self.allowed_domains:
            return True
        return domain.lower() in [d.lower() for d in self.allowed_domains]

    def get_session_timeout(self) -> int:
        """Get session timeout in minutes."""
        return self.get_security_setting("session_timeout_minutes", 60)

    def get_max_concurrent_sessions(self) -> int:
        """Get maximum concurrent sessions allowed."""
        return self.get_security_setting("max_concurrent_sessions", 5)

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()

    def update_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.update_activity()

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert tenant to dictionary for API responses."""
        data = {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "slug": self.slug,
            "status": self.status.value,
            "plan": self.plan.value,
            "admin_email": self.admin_email,
            "admin_name": self.admin_name,
            "primary_domain": self.primary_domain,
            "features_enabled": self.features_enabled,
            "limits": self.limits,
            "usage_stats": self.usage_stats,
            "is_active": self.is_active(),
            "is_trial": self.is_trial(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None
        }

        if include_sensitive:
            data.update({
                "external_id": self.external_id,
                "allowed_domains": self.allowed_domains,
                "security_settings": self.security_settings,
                "integrations": self.integrations,
                "billing_email": self.billing_email,
                "subscription_start": self.subscription_start.isoformat() if self.subscription_start else None,
                "subscription_end": self.subscription_end.isoformat() if self.subscription_end else None,
                "trial_end": self.trial_end.isoformat() if self.trial_end else None
            })

        return data
