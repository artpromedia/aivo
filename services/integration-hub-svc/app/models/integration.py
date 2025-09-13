"""Integration connector models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlalchemy import String, Text, Boolean, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .tenant import Tenant


class ConnectorType(str, Enum):
    """Types of integration connectors."""

    GOOGLE_CLASSROOM = "google_classroom"
    CANVAS_LTI = "canvas_lti"
    ZOOM_LTI = "zoom_lti"
    CLEVER = "clever"
    ONEROSTER = "oneroster"


class ConnectionStatus(str, Enum):
    """Connection status for integrations."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    EXPIRED = "expired"


class LogLevel(str, Enum):
    """Log levels for connection logs."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Integration(Base, TimestampMixin):
    """Integration connector configuration."""

    __tablename__ = "integrations"

    # Basic Information
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Connector Configuration
    connector_type: Mapped[ConnectorType] = mapped_column(
        SQLEnum(ConnectorType),
        nullable=False,
        index=True,
    )
    status: Mapped[ConnectionStatus] = mapped_column(
        SQLEnum(ConnectionStatus),
        default=ConnectionStatus.DISCONNECTED,
        nullable=False,
        index=True,
    )

    # Authentication & Configuration
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    credentials: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)  # Encrypted

    # Connection Details
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_error_message: Mapped[Optional[str]] = mapped_column(Text)

    # OAuth Configuration
    oauth_client_id: Mapped[Optional[str]] = mapped_column(String(255))
    oauth_scopes: Mapped[Optional[list[str]]] = mapped_column(JSON)
    oauth_redirect_uri: Mapped[Optional[str]] = mapped_column(String(500))

    # Rate Limiting
    rate_limit_per_hour: Mapped[Optional[int]] = mapped_column(default=1000)
    requests_today: Mapped[int] = mapped_column(default=0, nullable=False)
    requests_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    updated_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    connection_logs: Mapped[list["ConnectionLog"]] = relationship(
        back_populates="integration",
        cascade="all, delete-orphan",
        order_by="ConnectionLog.created_at.desc()",
    )
    tests: Mapped[list["IntegrationTest"]] = relationship(
        back_populates="integration",
        cascade="all, delete-orphan",
        order_by="IntegrationTest.created_at.desc()",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Integration(id={self.id}, name='{self.name}', type='{self.connector_type}', status='{self.status}')>"


class ConnectionLog(Base, TimestampMixin):
    """Connection activity logs."""

    __tablename__ = "connection_logs"

    # Relationships
    integration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Log Details
    level: Mapped[LogLevel] = mapped_column(
        SQLEnum(LogLevel),
        default=LogLevel.INFO,
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Context
    operation: Mapped[Optional[str]] = mapped_column(String(100))  # connect, sync, test, etc.
    duration_ms: Mapped[Optional[int]] = mapped_column()
    request_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Error Information
    error_code: Mapped[Optional[str]] = mapped_column(String(100))
    error_type: Mapped[Optional[str]] = mapped_column(String(100))
    stack_trace: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    integration: Mapped["Integration"] = relationship(back_populates="connection_logs")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ConnectionLog(id={self.id}, level='{self.level}', operation='{self.operation}')>"


class IntegrationTest(Base, TimestampMixin):
    """Integration connection test results."""

    __tablename__ = "integration_tests"

    # Relationships
    integration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Test Configuration
    test_type: Mapped[str] = mapped_column(String(100), nullable=False)  # connection, auth, sync, etc.
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Test Results
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column()
    message: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Test Data
    request_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    response_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Metadata
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    triggered_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    integration: Mapped["Integration"] = relationship(back_populates="tests")

    def __repr__(self) -> str:
        """String representation."""
        return f"<IntegrationTest(id={self.id}, type='{self.test_type}', success={self.success})>"


class ConnectorConfig(Base, TimestampMixin):
    """Global connector configuration and metadata."""

    __tablename__ = "connector_configs"

    # Connector Information
    connector_type: Mapped[ConnectorType] = mapped_column(
        SQLEnum(ConnectorType),
        nullable=False,
        unique=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Configuration
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # OAuth Configuration
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(100))
    oauth_auth_url: Mapped[Optional[str]] = mapped_column(String(500))
    oauth_token_url: Mapped[Optional[str]] = mapped_column(String(500))
    oauth_scopes: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # API Configuration
    base_url: Mapped[Optional[str]] = mapped_column(String(500))
    api_version: Mapped[Optional[str]] = mapped_column(String(50))
    rate_limit_per_hour: Mapped[int] = mapped_column(default=1000, nullable=False)

    # Documentation
    documentation_url: Mapped[Optional[str]] = mapped_column(String(500))
    support_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Metadata
    version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ConnectorConfig(type='{self.connector_type}', name='{self.display_name}')>"
