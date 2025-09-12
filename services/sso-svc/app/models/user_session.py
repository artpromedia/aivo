"""
User Session model for managing SSO sessions.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin, TimestampMixin, TenantMixin


class SessionStatus(str, Enum):
    """User session status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    INVALID = "invalid"


class UserSession(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    User Session model for tracking SSO sessions.

    Manages user authentication sessions, including SAML session tracking,
    session timeouts, and multi-device session management.
    """

    __tablename__ = "user_sessions"

    # User identification
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Session identification
    session_token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    saml_session_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)

    # Provider information
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_providers.id"),
        nullable=False,
        index=True
    )

    # Session status and timing
    status: Mapped[SessionStatus] = mapped_column(
        SQLEnum(SessionStatus),
        nullable=False,
        default=SessionStatus.ACTIVE
    )

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Authentication details
    authentication_method: Mapped[str] = mapped_column(String(50), nullable=False, default="saml")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 support
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # User attributes from SAML assertion
    user_attributes: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {}
    )

    # Roles and permissions
    roles: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: []
    )
    permissions: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: []
    )

    # Session metadata
    device_info: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {}
    )

    # Termination information
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id='{self.user_id}', status='{self.status}')>"

    def is_active(self) -> bool:
        """Check if session is active and not expired."""
        return (
            self.status == SessionStatus.ACTIVE and
            datetime.utcnow() < self.expires_at
        )

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() >= self.expires_at

    def extend_session(self, minutes: int = 60) -> None:
        """Extend session expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.last_activity_at = datetime.utcnow()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()

    def terminate(self, reason: str = "logout") -> None:
        """Terminate the session."""
        self.status = SessionStatus.TERMINATED
        self.terminated_at = datetime.utcnow()
        self.termination_reason = reason

    def expire(self) -> None:
        """Mark session as expired."""
        self.status = SessionStatus.EXPIRED
        if not self.terminated_at:
            self.terminated_at = datetime.utcnow()
            self.termination_reason = "expired"

    def get_user_attribute(self, attribute: str, default: Any = None) -> Any:
        """Get user attribute from SAML assertion."""
        return self.user_attributes.get(attribute, default)

    def set_user_attribute(self, attribute: str, value: Any) -> None:
        """Set user attribute from SAML assertion."""
        if self.user_attributes is None:
            self.user_attributes = {}
        self.user_attributes[attribute] = value

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in (self.roles or [])

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in (self.permissions or [])

    def add_role(self, role: str) -> None:
        """Add role to user session."""
        if self.roles is None:
            self.roles = []
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: str) -> None:
        """Remove role from user session."""
        if self.roles and role in self.roles:
            self.roles.remove(role)

    def add_permission(self, permission: str) -> None:
        """Add permission to user session."""
        if self.permissions is None:
            self.permissions = []
        if permission not in self.permissions:
            self.permissions.append(permission)

    def get_session_duration(self) -> timedelta:
        """Get session duration since creation."""
        return datetime.utcnow() - self.created_at

    def get_time_until_expiry(self) -> timedelta:
        """Get time remaining until session expires."""
        return self.expires_at - datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "email": self.email,
            "status": self.status.value,
            "expires_at": self.expires_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat(),
            "roles": self.roles,
            "permissions": self.permissions,
            "is_active": self.is_active(),
            "time_until_expiry": str(self.get_time_until_expiry()) if self.is_active() else None
        }
