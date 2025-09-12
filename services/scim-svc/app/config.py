"""
Configuration management for SCIM Service.
"""

import os
from functools import lru_cache
from typing import List, Dict, Any

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    environment: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    port: int = Field(default=8002, description="Application port")

    # SCIM Configuration
    base_url: str = Field(
        default="https://api.aivo.com/scim/v2",
        description="SCIM service base URL"
    )
    max_results: int = Field(default=200, description="Maximum results per page")
    default_count: int = Field(default=20, description="Default page size")

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://scim_user:scim_password@localhost:5432/scim_db",
        description="Async PostgreSQL database URL"
    )
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=30, description="Database connection max overflow")

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/1", description="Redis URL for caching")
    redis_session_ttl: int = Field(default=3600, description="Redis session TTL in seconds")
    redis_cache_ttl: int = Field(default=300, description="Redis cache TTL in seconds")

    # Security settings
    secret_key: str = Field(default="your-secret-key-change-in-production", description="Application secret key")

    # Authentication settings
    bearer_token: str = Field(
        default="scim-bearer-token-change-in-production",
        description="Default SCIM bearer token"
    )
    oauth_client_id: str = Field(default="", description="OAuth 2.0 client ID")
    oauth_client_secret: str = Field(default="", description="OAuth 2.0 client secret")
    oauth_token_url: str = Field(default="", description="OAuth 2.0 token endpoint")

    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.aivo.local"],
        description="Allowed host headers"
    )

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=1000, description="API rate limit per minute")
    rate_limit_burst_size: int = Field(default=100, description="Rate limit burst capacity")
    rate_limit_per_tenant: bool = Field(default=True, description="Enable per-tenant rate limiting")

    # Webhook settings
    webhook_base_url: str = Field(default="", description="Base URL for webhook notifications")
    webhook_secret: str = Field(default="webhook-secret-change-in-production", description="Webhook HMAC secret")
    webhook_timeout: int = Field(default=30, description="Webhook request timeout in seconds")
    webhook_retries: int = Field(default=3, description="Number of webhook delivery retries")

    # Multi-tenancy settings
    multi_tenant_enabled: bool = Field(default=True, description="Enable multi-tenancy support")
    tenant_isolation_strict: bool = Field(default=True, description="Strict tenant data isolation")
    default_tenant_id: str = Field(default="default", description="Default tenant ID")

    # SCIM Provider Configuration
    service_provider_config: Dict[str, Any] = Field(
        default={
            "documentationUri": "https://docs.aivo.com/scim",
            "patch": {"supported": True},
            "bulk": {
                "supported": True,
                "maxOperations": 1000,
                "maxPayloadSize": 1048576  # 1MB
            },
            "filter": {
                "supported": True,
                "maxResults": 200
            },
            "changePassword": {"supported": False},
            "sort": {"supported": True},
            "etag": {"supported": True},
            "authenticationSchemes": [
                {
                    "name": "OAuth Bearer Token",
                    "description": "Authentication scheme using the OAuth 2.0 Bearer Token Standard",
                    "specUri": "http://www.rfc-editor.org/info/rfc6750",
                    "documentationUri": "https://docs.aivo.com/scim/auth",
                    "type": "oauthbearertoken",
                    "primary": True
                },
                {
                    "name": "HTTP Basic",
                    "description": "Authentication scheme using the HTTP Basic Standard",
                    "specUri": "http://www.rfc-editor.org/info/rfc2617",
                    "documentationUri": "https://docs.aivo.com/scim/auth",
                    "type": "httpbasic",
                    "primary": False
                }
            ]
        }
    )

    # Custom Schema Configuration
    custom_schemas: Dict[str, Dict[str, Any]] = Field(
        default={
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
                "id": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                "name": "Enterprise User",
                "description": "Enterprise extension to the User resource",
                "attributes": [
                    {
                        "name": "employeeNumber",
                        "type": "string",
                        "multiValued": False,
                        "description": "Numeric or alphanumeric identifier assigned to a person",
                        "required": False,
                        "caseExact": False,
                        "mutability": "readWrite",
                        "returned": "default",
                        "uniqueness": "none"
                    },
                    {
                        "name": "costCenter",
                        "type": "string",
                        "multiValued": False,
                        "description": "Cost center for the user",
                        "required": False,
                        "caseExact": False,
                        "mutability": "readWrite",
                        "returned": "default",
                        "uniqueness": "none"
                    },
                    {
                        "name": "organization",
                        "type": "string",
                        "multiValued": False,
                        "description": "Organization that the user belongs to",
                        "required": False,
                        "caseExact": False,
                        "mutability": "readWrite",
                        "returned": "default",
                        "uniqueness": "none"
                    },
                    {
                        "name": "division",
                        "type": "string",
                        "multiValued": False,
                        "description": "Division within the organization",
                        "required": False,
                        "caseExact": False,
                        "mutability": "readWrite",
                        "returned": "default",
                        "uniqueness": "none"
                    },
                    {
                        "name": "department",
                        "type": "string",
                        "multiValued": False,
                        "description": "Department within the organization",
                        "required": False,
                        "caseExact": False,
                        "mutability": "readWrite",
                        "returned": "default",
                        "uniqueness": "none"
                    },
                    {
                        "name": "manager",
                        "type": "complex",
                        "multiValued": False,
                        "description": "Manager of the user",
                        "required": False,
                        "subAttributes": [
                            {
                                "name": "value",
                                "type": "string",
                                "multiValued": False,
                                "description": "The id of the SCIM resource representing the User's manager",
                                "required": False,
                                "caseExact": False,
                                "mutability": "readWrite",
                                "returned": "default",
                                "uniqueness": "none"
                            },
                            {
                                "name": "$ref",
                                "type": "reference",
                                "referenceTypes": ["User"],
                                "multiValued": False,
                                "description": "URI of the SCIM resource representing the User's manager",
                                "required": False,
                                "caseExact": False,
                                "mutability": "readWrite",
                                "returned": "default",
                                "uniqueness": "none"
                            },
                            {
                                "name": "displayName",
                                "type": "string",
                                "multiValued": False,
                                "description": "The displayName of the User's manager",
                                "required": False,
                                "caseExact": False,
                                "mutability": "readOnly",
                                "returned": "default",
                                "uniqueness": "none"
                            }
                        ],
                        "mutability": "readWrite",
                        "returned": "default",
                        "uniqueness": "none"
                    }
                ]
            }
        }
    )

    # OpenTelemetry settings
    otlp_endpoint: str | None = Field(default=None, description="OTLP collector endpoint")
    otel_resource_attributes: str = Field(
        default="service.name=scim-svc,service.version=0.1.0",
        description="OpenTelemetry resource attributes"
    )

    # Audit logging
    audit_log_enabled: bool = Field(default=True, description="Enable audit logging")
    audit_log_retention_days: int = Field(default=90, description="Audit log retention in days")

    # Performance settings
    batch_size: int = Field(default=100, description="Default batch processing size")
    bulk_operation_timeout: int = Field(default=300, description="Bulk operation timeout in seconds")

    # Tenant-specific configuration
    tenant_configs: Dict[str, Dict[str, Any]] = Field(
        default={},
        description="Tenant-specific configurations"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if field_name in ["cors_origins", "allowed_hosts"]:
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

    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """Get configuration for a specific tenant."""
        return self.tenant_configs.get(tenant_id, {})

    def get_tenant_bearer_token(self, tenant_id: str) -> str:
        """Get bearer token for a specific tenant."""
        tenant_config = self.get_tenant_config(tenant_id)
        return tenant_config.get("bearer_token", self.bearer_token)

    def get_tenant_webhook_url(self, tenant_id: str) -> str | None:
        """Get webhook URL for a specific tenant."""
        tenant_config = self.get_tenant_config(tenant_id)
        return tenant_config.get("webhook_url")

    def get_tenant_custom_schemas(self, tenant_id: str) -> List[str]:
        """Get custom schemas for a specific tenant."""
        tenant_config = self.get_tenant_config(tenant_id)
        return tenant_config.get("custom_schemas", [])


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
