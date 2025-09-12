"""
Configuration management for SSO Service.
"""

import os
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    port: int = Field(default=8001, description="Application port")

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://sso_user:sso_password@localhost:5432/sso_db",
        description="Async PostgreSQL database URL"
    )
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=30, description="Database connection max overflow")

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL for caching")
    redis_session_ttl: int = Field(default=3600, description="Redis session TTL in seconds")
    redis_cache_ttl: int = Field(default=300, description="Redis cache TTL in seconds")

    # Security settings
    secret_key: str = Field(default="your-secret-key-change-in-production", description="Application secret key")
    jwt_secret_key: str = Field(default="your-jwt-secret-key", description="JWT signing secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration in hours")

    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.aivo.local"],
        description="Allowed host headers"
    )

    # SAML settings
    saml_sp_entity_id: str = Field(
        default="https://aivo.local/sso/saml/metadata",
        description="SAML Service Provider Entity ID"
    )
    saml_sp_assertion_consumer_service: str = Field(
        default="https://aivo.local/sso/saml/acs",
        description="SAML ACS endpoint URL"
    )
    saml_sp_single_logout_service: str = Field(
        default="https://aivo.local/sso/saml/sls",
        description="SAML SLS endpoint URL"
    )
    saml_certificate_file: str = Field(
        default="./certs/saml.crt",
        description="SAML certificate file path"
    )
    saml_private_key_file: str = Field(
        default="./certs/saml.key",
        description="SAML private key file path"
    )
    saml_sign_requests: bool = Field(default=True, description="Sign SAML requests")
    saml_encrypt_assertions: bool = Field(default=True, description="Encrypt SAML assertions")

    # SCIM settings
    scim_endpoint_base: str = Field(
        default="https://aivo.local/scim/v2",
        description="SCIM 2.0 endpoint base URL"
    )
    scim_bearer_token: str = Field(
        default="scim-bearer-token-change-in-production",
        description="SCIM API bearer token"
    )

    # OpenTelemetry settings
    otlp_endpoint: str | None = Field(default=None, description="OTLP collector endpoint")
    otel_resource_attributes: str = Field(
        default="service.name=sso-svc,service.version=0.1.0",
        description="OpenTelemetry resource attributes"
    )

    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, description="API rate limit per minute")
    rate_limit_burst: int = Field(default=20, description="Rate limit burst capacity")

    # Session management
    session_timeout_minutes: int = Field(default=60, description="Session timeout in minutes")
    max_concurrent_sessions: int = Field(default=5, description="Max concurrent sessions per user")

    # JIT provisioning settings
    jit_provisioning_enabled: bool = Field(default=True, description="Enable Just-In-Time user provisioning")
    jit_default_role: str = Field(default="viewer", description="Default role for JIT provisioned users")
    jit_allowed_domains: List[str] = Field(
        default=["@company.com", "@trusted-partner.com"],
        description="Allowed email domains for JIT provisioning"
    )

    # Multi-tenancy settings
    multi_tenant_enabled: bool = Field(default=True, description="Enable multi-tenancy support")
    tenant_isolation_strict: bool = Field(default=True, description="Strict tenant data isolation")

    # Audit logging
    audit_log_enabled: bool = Field(default=True, description="Enable audit logging")
    audit_log_retention_days: int = Field(default=90, description="Audit log retention in days")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if field_name in ["cors_origins", "allowed_hosts", "jit_allowed_domains"]:
                return [item.strip() for item in raw_val.split(",")]
            return cls.json_loads(raw_val)

    def get_database_url(self) -> str:
        """Get database URL with proper formatting."""
        return self.database_url

    def get_redis_url(self) -> str:
        """Get Redis URL with proper formatting."""
        return self.redis_url

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
