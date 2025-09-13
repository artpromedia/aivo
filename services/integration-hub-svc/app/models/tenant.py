"""Tenant model for multi-tenancy support."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .api_key import ApiKey
    from .webhook import Webhook


class Tenant(Base, TimestampMixin):
    """Tenant model for multi-tenancy."""

    __tablename__ = "tenants"

    # Basic Information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Contact Information
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_name: Mapped[str | None] = mapped_column(String(255))

    # Configuration
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    max_api_keys: Mapped[int] = mapped_column(default=10, nullable=False)
    max_webhooks: Mapped[int] = mapped_column(default=50, nullable=False)

    # Relationships
    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    webhooks: Mapped[list["Webhook"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}')>"
