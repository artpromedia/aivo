"""Configuration settings for the Audit Log Service."""

import secrets
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "Audit Log Service"
    version: str = "0.1.0"
    description: str = "Immutable Audit Logging Service with WORM compliance"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8400
    reload: bool = False
    workers: int = 1

    # Security
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"

    # Database Configuration (WORM-compliant)
    database_hostname: str = "localhost"
    database_port: int = 5432
    database_username: str = "postgres"
    database_password: str = "password"
    database_name: str = "audit_logs"
    database_pool_size: int = 20
    database_max_overflow: int = 50
    database_echo: bool = False

    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> PostgresDsn:
        """Build database URL from components."""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.database_username,
            password=self.database_password,
            host=self.database_hostname,
            port=self.database_port,
            path=self.database_name,
        )

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 1
    redis_pool_size: int = 10

    @computed_field  # type: ignore[misc]
    @property
    def redis_url(self) -> RedisDsn:
        """Build Redis URL from components."""
        return RedisDsn.build(
            scheme="redis",
            password=self.redis_password,
            host=self.redis_host,
            port=self.redis_port,
            path=str(self.redis_db),
        )

    # AWS S3 Configuration for exports
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "aivo-audit-exports"
    s3_export_prefix: str = "audit-logs"

    # Audit Configuration
    enable_hash_chain: bool = True
    hash_algorithm: str = "sha256"
    retention_days: int = 2555  # 7 years for compliance

    # Export Configuration
    export_signed_url_expiry_hours: int = 24
    max_export_records: int = 100000
    export_formats: list[str] = ["csv", "json", "xlsx"]

    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = True
    jaeger_endpoint: Optional[str] = None
    log_level: str = "INFO"

    # Rate Limiting
    rate_limit_requests_per_minute: int = 1000
    rate_limit_burst: int = 2000

    # Environment
    environment: str = "development"
    debug: bool = False

    # Compliance & Security
    require_tamper_check: bool = True
    enable_real_time_monitoring: bool = True
    alert_on_tampering: bool = True

    # Pagination limits
    default_page_size: int = 50
    max_page_size: int = 1000


# Global settings instance
settings = Settings()
