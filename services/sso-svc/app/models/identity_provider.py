"""
Identity Provider model for SAML and OAuth configurations.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, TYPE_CHECKING

from sqlalchemy import Boolean, JSON, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .role_mapping import RoleMapping


class ProviderType(str, Enum):
    """Identity provider types."""

    SAML = "saml"
    OAUTH2 = "oauth2"
    OIDC = "oidc"
    LDAP = "ldap"


class ProviderStatus(str, Enum):
    """Identity provider status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"


class IdentityProvider(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    """
    Identity Provider configuration model.

    Stores SAML, OAuth2, OIDC, and LDAP provider configurations
    for enterprise SSO integration.
    """

    __tablename__ = "identity_providers"

    # Basic provider information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provider type and status
    provider_type: Mapped[ProviderType] = mapped_column(
        SQLEnum(ProviderType),
        nullable=False,
        default=ProviderType.SAML
    )
    status: Mapped[ProviderStatus] = mapped_column(
        SQLEnum(ProviderStatus),
        nullable=False,
        default=ProviderStatus.PENDING
    )

    # Provider configuration
    entity_id: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    metadata_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    metadata_xml: Mapped[str | None] = mapped_column(Text, nullable=True)

    # SAML specific settings
    sso_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    slo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    certificate: Mapped[str | None] = mapped_column(Text, nullable=True)

    # OAuth2/OIDC specific settings
    client_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    client_secret: Mapped[str | None] = mapped_column(String(500), nullable=True)
    authorization_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    token_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    userinfo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    jwks_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # LDAP specific settings
    ldap_server: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ldap_port: Mapped[int | None] = mapped_column(nullable=True)
    ldap_bind_dn: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ldap_bind_password: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ldap_user_base: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ldap_user_filter: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Security and encryption settings
    sign_requests: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    encrypt_assertions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    want_assertions_signed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    want_response_signed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # JIT provisioning settings
    jit_provisioning_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    jit_update_on_login: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Attribute mappings and configuration
    attribute_mappings: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            "first_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
            "last_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
            "display_name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
            "groups": "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups"
        }
    )

    # Advanced configuration options
    advanced_settings: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "session_timeout": 3600,
            "force_authn": False,
            "allow_unsolicited": False,
            "signature_algorithm": "RSA_SHA256",
            "digest_algorithm": "SHA256"
        }
    )

    # Domain restrictions
    allowed_domains: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None
    )

    # Provider ordering and visibility
    display_order: Mapped[int] = mapped_column(nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Connection testing
    last_test_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_test_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_test_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    role_mappings: Mapped[list["RoleMapping"]] = relationship(
        "RoleMapping",
        back_populates="provider",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<IdentityProvider(id={self.id}, name='{self.name}', type='{self.provider_type}')>"

    def is_saml_provider(self) -> bool:
        """Check if this is a SAML provider."""
        return self.provider_type == ProviderType.SAML

    def is_oauth_provider(self) -> bool:
        """Check if this is an OAuth2/OIDC provider."""
        return self.provider_type in [ProviderType.OAUTH2, ProviderType.OIDC]

    def is_ldap_provider(self) -> bool:
        """Check if this is an LDAP provider."""
        return self.provider_type == ProviderType.LDAP

    def is_active(self) -> bool:
        """Check if provider is active and not deleted."""
        return self.status == ProviderStatus.ACTIVE and not self.is_deleted

    def get_attribute_mapping(self, attribute: str) -> str | None:
        """Get SAML attribute mapping for a user attribute."""
        return self.attribute_mappings.get(attribute)

    def set_attribute_mapping(self, attribute: str, saml_attribute: str) -> None:
        """Set SAML attribute mapping for a user attribute."""
        if self.attribute_mappings is None:
            self.attribute_mappings = {}
        self.attribute_mappings[attribute] = saml_attribute

    def get_advanced_setting(self, setting: str, default: Any = None) -> Any:
        """Get advanced configuration setting."""
        if self.advanced_settings is None:
            return default
        return self.advanced_settings.get(setting, default)

    def set_advanced_setting(self, setting: str, value: Any) -> None:
        """Set advanced configuration setting."""
        if self.advanced_settings is None:
            self.advanced_settings = {}
        self.advanced_settings[setting] = value

    def is_domain_allowed(self, email: str) -> bool:
        """Check if email domain is allowed for this provider."""
        if not self.allowed_domains:
            return True

        email_domain = email.split("@")[-1].lower()
        return email_domain in [domain.lower() for domain in self.allowed_domains]
