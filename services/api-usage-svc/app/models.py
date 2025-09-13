"""Database models for API usage service."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class LimitType(str, Enum):
    """Rate limit types."""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    REQUESTS_PER_MONTH = "requests_per_month"
    BANDWIDTH_PER_MINUTE = "bandwidth_per_minute"
    BANDWIDTH_PER_HOUR = "bandwidth_per_hour"
    BANDWIDTH_PER_DAY = "bandwidth_per_day"


class RequestStatus(str, Enum):
    """Request increase ticket status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class ApiUsage(Base):
    """API usage tracking model."""

    __tablename__ = "api_usage"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)
    route_path = Column(String, nullable=False, index=True)
    method = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Request details
    request_size_bytes = Column(Integer, default=0)
    response_size_bytes = Column(Integer, default=0)
    response_time_ms = Column(Float, default=0.0)
    status_code = Column(Integer, nullable=False)

    # User/client info
    user_id = Column(String, nullable=True, index=True)
    client_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Rate limiting
    rate_limited = Column(Boolean, default=False)
    rate_limit_reason = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RateLimit(Base):
    """Rate limit configuration model."""

    __tablename__ = "rate_limits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)
    route_pattern = Column(String, nullable=False)  # e.g., "/api/v1/secrets/*"

    # Limit configuration
    limit_type = Column(String, nullable=False)  # LimitType enum
    limit_value = Column(Integer, nullable=False)
    current_usage = Column(Integer, default=0)

    # Time window
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)

    # Status
    enabled = Column(Boolean, default=True)
    enforcement_mode = Column(String, default="enforce")  # enforce, warn, monitor

    # Metadata
    description = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class RateLimitBreach(Base):
    """Rate limit breach tracking model."""

    __tablename__ = "rate_limit_breaches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rate_limit_id = Column(String, ForeignKey("rate_limits.id"), nullable=False)
    tenant_id = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False)
    route_path = Column(String, nullable=False)

    # Breach details
    breach_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    attempted_requests = Column(Integer, nullable=False)
    allowed_limit = Column(Integer, nullable=False)
    breach_percentage = Column(Float, nullable=False)  # How much over the limit

    # Context
    user_id = Column(String, nullable=True)
    client_ip = Column(String, nullable=True)
    action_taken = Column(String, nullable=False)  # throttled, blocked, warned

    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    rate_limit = relationship("RateLimit", backref="breaches")


class QuotaIncreaseRequest(Base):
    """Quota increase request model."""

    __tablename__ = "quota_increase_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False)
    route_pattern = Column(String, nullable=False)

    # Current and requested limits
    current_limit = Column(Integer, nullable=False)
    requested_limit = Column(Integer, nullable=False)
    limit_type = Column(String, nullable=False)  # LimitType enum

    # Request details
    justification = Column(Text, nullable=False)
    business_impact = Column(Text, nullable=True)
    expected_usage_pattern = Column(Text, nullable=True)
    duration_needed = Column(String, nullable=True)  # temporary, permanent

    # Approval workflow
    status = Column(String, default=RequestStatus.PENDING.value, nullable=False)
    requested_by = Column(String, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Approval details
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_limit = Column(Integer, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Implementation
    implemented_by = Column(String, nullable=True)
    implemented_at = Column(DateTime, nullable=True)
    implementation_notes = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ApiQuota(Base):
    """API quota management model."""

    __tablename__ = "api_quotas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)

    # Quota configuration
    monthly_request_limit = Column(Integer, default=10000)
    daily_request_limit = Column(Integer, default=1000)
    hourly_request_limit = Column(Integer, default=100)

    # Current usage
    monthly_usage = Column(Integer, default=0)
    daily_usage = Column(Integer, default=0)
    hourly_usage = Column(Integer, default=0)

    # Reset timestamps
    monthly_reset_at = Column(DateTime, nullable=True)
    daily_reset_at = Column(DateTime, nullable=True)
    hourly_reset_at = Column(DateTime, nullable=True)

    # Status
    enabled = Column(Boolean, default=True)
    soft_limit_enabled = Column(Boolean, default=True)
    soft_limit_percentage = Column(Float, default=0.8)  # Warn at 80%

    # Metadata
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
