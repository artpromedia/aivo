"""
Audit Log model for security and compliance tracking.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any

from sqlalchemy import JSON, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin, TenantMixin


class AuditEventType(str, Enum):
    """Audit event types."""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    SESSION_TIMEOUT = "session_timeout"

    # User management events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ROLE_CHANGED = "user_role_changed"

    # Provider management events
    PROVIDER_CREATED = "provider_created"
    PROVIDER_UPDATED = "provider_updated"
    PROVIDER_DELETED = "provider_deleted"
    PROVIDER_TEST = "provider_test"

    # Role mapping events
    ROLE_MAPPING_CREATED = "role_mapping_created"
    ROLE_MAPPING_UPDATED = "role_mapping_updated"
    ROLE_MAPPING_DELETED = "role_mapping_deleted"
    ROLE_MAPPING_APPLIED = "role_mapping_applied"

    # SCIM events
    SCIM_USER_PROVISIONED = "scim_user_provisioned"
    SCIM_USER_UPDATED = "scim_user_updated"
    SCIM_USER_DEPROVISIONED = "scim_user_deprovisioned"
    SCIM_GROUP_SYNC = "scim_group_sync"

    # Security events
    INVALID_SAML_RESPONSE = "invalid_saml_response"
    CERTIFICATE_VALIDATION_FAILED = "certificate_validation_failed"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # System events
    CONFIGURATION_CHANGED = "configuration_changed"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    ERROR_OCCURRED = "error_occurred"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base, UUIDMixin, TenantMixin):
    """
    Audit Log model for security and compliance tracking.

    Records all important security events, user actions, and system changes
    for compliance, security monitoring, and troubleshooting.
    """

    __tablename__ = "audit_logs"

    # Event information
    event_type: Mapped[AuditEventType] = mapped_column(
        SQLEnum(AuditEventType),
        nullable=False,
        index=True
    )
    severity: Mapped[AuditSeverity] = mapped_column(
        SQLEnum(AuditSeverity),
        nullable=False,
        default=AuditSeverity.LOW,
        index=True
    )

    # Event timestamp (separate from created_at for precise event timing)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Actor information (who performed the action)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, system, service, admin
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    actor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Target information (what was affected)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # user, provider, mapping, session
    target_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    target_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Event details
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Technical details
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)

    # Provider context
    provider_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    provider_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Event outcome
    success: Mapped[bool | None] = mapped_column(nullable=True, index=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Additional context and metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {}
    )

    # Changes tracking (before/after for updates)
    changes_before: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    changes_after: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Compliance and retention
    retention_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_sensitive: Mapped[bool] = mapped_column(nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', actor='{self.actor_id}')>"

    @classmethod
    def create_login_event(
        cls,
        success: bool,
        user_id: str | None = None,
        email: str | None = None,
        provider_id: uuid.UUID | None = None,
        provider_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        error_message: str | None = None,
        tenant_id: uuid.UUID | None = None,
        **metadata
    ) -> "AuditLog":
        """Create a login audit event."""
        return cls(
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
            severity=AuditSeverity.LOW if success else AuditSeverity.MEDIUM,
            actor_type="user",
            actor_id=user_id,
            actor_email=email,
            target_type="session",
            action="login",
            description=f"User login {'successful' if success else 'failed'}",
            ip_address=ip_address,
            user_agent=user_agent,
            provider_id=provider_id,
            provider_name=provider_name,
            success=success,
            error_message=error_message,
            tenant_id=tenant_id,
            metadata=metadata
        )

    @classmethod
    def create_user_event(
        cls,
        event_type: AuditEventType,
        user_id: str,
        email: str | None = None,
        actor_id: str | None = None,
        actor_email: str | None = None,
        changes_before: Dict[str, Any] | None = None,
        changes_after: Dict[str, Any] | None = None,
        tenant_id: uuid.UUID | None = None,
        **metadata
    ) -> "AuditLog":
        """Create a user management audit event."""
        action_map = {
            AuditEventType.USER_CREATED: "create",
            AuditEventType.USER_UPDATED: "update",
            AuditEventType.USER_DELETED: "delete",
            AuditEventType.USER_ROLE_CHANGED: "role_change"
        }

        return cls(
            event_type=event_type,
            severity=AuditSeverity.MEDIUM,
            actor_type="admin" if actor_id else "system",
            actor_id=actor_id,
            actor_email=actor_email,
            target_type="user",
            target_id=user_id,
            target_name=email,
            action=action_map.get(event_type, "unknown"),
            resource="user",
            description=f"User {action_map.get(event_type, 'modified')}",
            success=True,
            changes_before=changes_before,
            changes_after=changes_after,
            tenant_id=tenant_id,
            metadata=metadata
        )

    @classmethod
    def create_security_event(
        cls,
        event_type: AuditEventType,
        description: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        actor_id: str | None = None,
        error_message: str | None = None,
        tenant_id: uuid.UUID | None = None,
        **metadata
    ) -> "AuditLog":
        """Create a security-related audit event."""
        return cls(
            event_type=event_type,
            severity=AuditSeverity.HIGH,
            actor_type="user" if actor_id else "unknown",
            actor_id=actor_id,
            action="security_violation",
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=error_message,
            tenant_id=tenant_id,
            is_sensitive=True,
            metadata=metadata
        )

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the audit log entry."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value from the audit log entry."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)

    def is_security_relevant(self) -> bool:
        """Check if this audit log entry is security-relevant."""
        security_events = {
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.INVALID_SAML_RESPONSE,
            AuditEventType.CERTIFICATE_VALIDATION_FAILED,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.RATE_LIMIT_EXCEEDED
        }
        return self.event_type in security_events or self.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]

    def should_retain(self) -> bool:
        """Check if this audit log should be retained based on retention policy."""
        if self.retention_date is None:
            return True
        return datetime.utcnow() < self.retention_date

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary for API responses."""
        return {
            "id": str(self.id),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "event_timestamp": self.event_timestamp.isoformat(),
            "actor": {
                "type": self.actor_type,
                "id": self.actor_id,
                "email": self.actor_email,
                "name": self.actor_name
            },
            "target": {
                "type": self.target_type,
                "id": self.target_id,
                "name": self.target_name
            } if self.target_type else None,
            "action": self.action,
            "resource": self.resource,
            "description": self.description,
            "success": self.success,
            "error_message": self.error_message,
            "ip_address": self.ip_address,
            "provider": {
                "id": str(self.provider_id),
                "name": self.provider_name
            } if self.provider_id else None,
            "metadata": self.metadata if not self.is_sensitive else {"redacted": True}
        }
