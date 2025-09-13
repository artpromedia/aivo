"""Secret storage models with encryption and audit support."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import String, Text, Boolean, JSON, DateTime, Enum as SQLEnum, LargeBinary, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class SecretType(str, Enum):
    """Types of secrets that can be stored."""

    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    ENCRYPTION_KEY = "encryption_key"
    OAUTH_SECRET = "oauth_secret"
    WEBHOOK_SECRET = "webhook_secret"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"
    JWT_SECRET = "jwt_secret"
    EMAIL_PASSWORD = "email_password"
    SMS_API_KEY = "sms_api_key"
    OCR_API_KEY = "ocr_api_key"
    OPENAI_API_KEY = "openai_api_key"
    CUSTOM = "custom"


class SecretStatus(str, Enum):
    """Status of a secret."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    ROTATING = "rotating"
    COMPROMISED = "compromised"


class AccessLevel(str, Enum):
    """Access levels for secrets."""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"


class AuditAction(str, Enum):
    """Types of audit actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ROTATE = "rotate"
    EXPIRE = "expire"
    COMPROMISE = "compromise"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"


class Secret(Base, TimestampMixin):
    """Encrypted secret storage model."""

    __tablename__ = "secrets"

    # Basic Information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Namespace and Organization
    namespace: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )

    # Secret Classification
    secret_type: Mapped[SecretType] = mapped_column(
        SQLEnum(SecretType),
        nullable=False,
        index=True,
    )
    status: Mapped[SecretStatus] = mapped_column(
        SQLEnum(SecretStatus),
        default=SecretStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Encrypted Data
    encrypted_value: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    encryption_key_id: Mapped[str] = mapped_column(String(255), nullable=False)
    encryption_algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    salt: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Metadata
    tags: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)
    secret_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Access Control
    access_level: Mapped[AccessLevel] = mapped_column(
        SQLEnum(AccessLevel),
        default=AccessLevel.READ_ONLY,
        nullable=False,
    )
    allowed_services: Mapped[Optional[list[str]]] = mapped_column(JSON)
    allowed_users: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # Lifecycle Management
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rotation_interval_days: Mapped[Optional[int]] = mapped_column()
    auto_rotate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Usage Tracking
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    access_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Audit and Security
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    updated_by: Mapped[Optional[str]] = mapped_column(String(255))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deleted_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Version Control
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    previous_version_id: Mapped[Optional[str]] = mapped_column(String(36))

    # Relationships
    audit_logs: Mapped[list["SecretAuditLog"]] = relationship(
        back_populates="secret",
        cascade="all, delete-orphan",
        order_by="SecretAuditLog.created_at.desc()",
    )
    access_logs: Mapped[list["SecretAccessLog"]] = relationship(
        back_populates="secret",
        cascade="all, delete-orphan",
        order_by="SecretAccessLog.created_at.desc()",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Secret(id={self.id}, name='{self.name}', namespace='{self.namespace}', type='{self.secret_type}')>"


class SecretVersion(Base, TimestampMixin):
    """Secret version history for rollback capability."""

    __tablename__ = "secret_versions"

    # Relationships
    secret_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    # Version Information
    version_number: Mapped[int] = mapped_column(nullable=False)

    # Encrypted Data (snapshot)
    encrypted_value: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    encryption_key_id: Mapped[str] = mapped_column(String(255), nullable=False)
    encryption_algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    salt: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    nonce: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Metadata Snapshot
    metadata_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Audit Information
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    change_reason: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        """String representation."""
        return f"<SecretVersion(id={self.id}, secret_id={self.secret_id}, version={self.version_number})>"


class SecretAuditLog(Base, TimestampMixin):
    """Audit log for secret operations."""

    __tablename__ = "secret_audit_logs"

    # Relationships
    secret_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("secrets.id"),
        nullable=False,
        index=True,
    )

    # Audit Information
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True,
    )
    actor: Mapped[Optional[str]] = mapped_column(String(255))  # User or service
    actor_type: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Details
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Status
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    secret: Mapped["Secret"] = relationship(back_populates="audit_logs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<SecretAuditLog(id={self.id}, action='{self.action}', actor='{self.actor}')>"


class SecretAccessLog(Base, TimestampMixin):
    """Access log for secret usage tracking."""

    __tablename__ = "secret_access_logs"

    # Relationships
    secret_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("secrets.id"),
        nullable=False,
        index=True,
    )

    # Access Information
    accessor: Mapped[Optional[str]] = mapped_column(String(255))  # User or service
    accessor_type: Mapped[str] = mapped_column(String(50), default="service", nullable=False)

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    service_name: Mapped[Optional[str]] = mapped_column(String(100))
    request_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Access Details
    access_method: Mapped[str] = mapped_column(String(50), nullable=False)  # api, sdk, cli
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Performance
    response_time_ms: Mapped[Optional[int]] = mapped_column()

    # Relationships
    secret: Mapped["Secret"] = relationship(back_populates="access_logs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<SecretAccessLog(id={self.id}, accessor='{self.accessor}', success={self.success})>"


class Namespace(Base, TimestampMixin):
    """Namespace for organizing secrets."""

    __tablename__ = "namespaces"

    # Basic Information
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Organization
    tenant_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )
    parent_namespace: Mapped[Optional[str]] = mapped_column(String(100))

    # Configuration
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_secrets: Mapped[Optional[int]] = mapped_column()
    retention_days: Mapped[Optional[int]] = mapped_column()

    # Access Control
    allowed_users: Mapped[Optional[list[str]]] = mapped_column(JSON)
    allowed_services: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # Metadata
    tags: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON)

    # Audit
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    updated_by: Mapped[Optional[str]] = mapped_column(String(255))

    def __repr__(self) -> str:
        """String representation."""
        return f"<Namespace(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"
