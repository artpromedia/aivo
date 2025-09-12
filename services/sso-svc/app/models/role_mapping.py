"""
Role Mapping model for SAML attribute to application role mapping.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .identity_provider import IdentityProvider


class MappingType(str, Enum):
    """Role mapping types."""

    ATTRIBUTE = "attribute"
    GROUP = "group"
    EXPRESSION = "expression"
    DEFAULT = "default"


class MappingOperator(str, Enum):
    """Mapping comparison operators."""

    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    IN = "in"
    NOT_IN = "not_in"


class RoleMapping(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    """
    Role Mapping model for mapping SAML attributes to application roles.

    Supports various mapping strategies including direct attribute mapping,
    group membership, and complex expression-based mappings.
    """

    __tablename__ = "role_mappings"

    # Reference to identity provider
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_providers.id"),
        nullable=False,
        index=True
    )

    # Mapping configuration
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Mapping type and priority
    mapping_type: Mapped[MappingType] = mapped_column(
        SQLEnum(MappingType),
        nullable=False,
        default=MappingType.ATTRIBUTE
    )
    priority: Mapped[int] = mapped_column(nullable=False, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Source attribute/group configuration
    source_attribute: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_value: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    operator: Mapped[MappingOperator] = mapped_column(
        SQLEnum(MappingOperator),
        nullable=False,
        default=MappingOperator.EQUALS
    )

    # Target role configuration
    target_role: Mapped[str] = mapped_column(String(100), nullable=False)
    role_permissions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Advanced mapping conditions
    conditions: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {}
    )

    # Expression-based mapping (for complex logic)
    expression: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Default mapping settings
    is_default_mapping: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    apply_to_all_users: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # JIT provisioning settings specific to this mapping
    create_user_if_not_exists: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    update_user_attributes: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Additional attributes to map
    attribute_mappings: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {}
    )

    # Usage statistics
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    usage_count: Mapped[int] = mapped_column(nullable=False, default=0)

    # Relationship to identity provider
    provider: Mapped["IdentityProvider"] = relationship(
        "IdentityProvider",
        back_populates="role_mappings"
    )

    def __repr__(self) -> str:
        return f"<RoleMapping(id={self.id}, name='{self.name}', target_role='{self.target_role}')>"

    def is_active(self) -> bool:
        """Check if mapping is active and not deleted."""
        return self.is_enabled and not self.is_deleted

    def matches_attribute(self, attribute_value: str) -> bool:
        """
        Check if the given attribute value matches this mapping.

        Args:
            attribute_value: The SAML attribute value to check

        Returns:
            bool: True if the value matches the mapping conditions
        """
        if not self.is_active() or not self.source_value:
            return False

        match self.operator:
            case MappingOperator.EQUALS:
                return attribute_value == self.source_value
            case MappingOperator.CONTAINS:
                return self.source_value in attribute_value
            case MappingOperator.STARTS_WITH:
                return attribute_value.startswith(self.source_value)
            case MappingOperator.ENDS_WITH:
                return attribute_value.endswith(self.source_value)
            case MappingOperator.IN:
                values = [v.strip() for v in self.source_value.split(",")]
                return attribute_value in values
            case MappingOperator.NOT_IN:
                values = [v.strip() for v in self.source_value.split(",")]
                return attribute_value not in values
            case MappingOperator.REGEX:
                import re
                try:
                    return bool(re.search(self.source_value, attribute_value))
                except re.error:
                    return False
            case _:
                return False

    def matches_groups(self, user_groups: list[str]) -> bool:
        """
        Check if user groups match this mapping.

        Args:
            user_groups: List of user's group memberships

        Returns:
            bool: True if groups match the mapping conditions
        """
        if not self.is_active() or self.mapping_type != MappingType.GROUP:
            return False

        if not self.source_value:
            return False

        required_groups = [g.strip() for g in self.source_value.split(",")]

        match self.operator:
            case MappingOperator.EQUALS | MappingOperator.IN:
                return any(group in user_groups for group in required_groups)
            case MappingOperator.NOT_IN:
                return not any(group in user_groups for group in required_groups)
            case MappingOperator.CONTAINS:
                return any(
                    any(req_group in user_group for user_group in user_groups)
                    for req_group in required_groups
                )
            case _:
                return False

    def evaluate_expression(self, user_attributes: Dict[str, Any]) -> bool:
        """
        Evaluate expression-based mapping.

        Args:
            user_attributes: Dictionary of user SAML attributes

        Returns:
            bool: True if expression evaluates to true
        """
        if not self.is_active() or self.mapping_type != MappingType.EXPRESSION:
            return False

        if not self.expression:
            return False

        try:
            # Create a safe evaluation context
            context = {
                "user": user_attributes,
                "attributes": user_attributes,
                # Add safe functions if needed
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
            }

            # Evaluate the expression (in production, use a safer evaluator)
            return bool(eval(self.expression, {"__builtins__": {}}, context))
        except Exception:
            return False

    def get_mapped_attributes(self, user_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get additional user attributes based on this mapping.

        Args:
            user_attributes: User's SAML attributes

        Returns:
            Dict[str, Any]: Additional attributes to apply to user
        """
        if not self.attribute_mappings:
            return {}

        mapped_attrs = {}
        for target_attr, source_attr in self.attribute_mappings.items():
            if source_attr in user_attributes:
                mapped_attrs[target_attr] = user_attributes[source_attr]

        return mapped_attrs

    def increment_usage(self) -> None:
        """Increment usage statistics."""
        from datetime import datetime
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
