"""API Key model for authentication."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .tenant import Tenant


class ApiKey(Base, TimestampMixin):
    """API Key model for tenant authentication."""

    __tablename__ = "api_keys"

    # Foreign Keys
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Key Information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Status and Permissions
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Usage Tracking
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Permissions (JSON array of scopes)
    scopes: Mapped[list[str]] = mapped_column(
        default=["read", "write"],
        nullable=False,
    )

    # Rate Limiting
    rate_limit_per_minute: Mapped[int | None] = mapped_column()

    # Audit Fields
    created_by: Mapped[str | None] = mapped_column(String(255))
    revoked_by: Mapped[str | None] = mapped_column(String(255))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_reason: Mapped[str | None] = mapped_column(Text)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="api_keys")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ApiKey(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the API key is valid for use."""
        return self.is_active and not self.is_revoked and not self.is_expired
