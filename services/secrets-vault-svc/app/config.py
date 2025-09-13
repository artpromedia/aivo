"""Configuration settings for the Secrets Vault Service."""

import secrets
from typing import Optional, List

from pydantic import Field, computed_field
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
    project_name: str = "Secrets Vault Service"
    version: str = "0.1.0"
    description: str = "Encrypted secrets and keys management service"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8400
    reload: bool = False
    workers: int = 1

    # Security
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"

    # Database Configuration
    database_hostname: str = "localhost"
    database_port: int = 5432
    database_username: str = "postgres"
    database_password: str = "password"
    database_name: str = "secrets_vault"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        """Build database URL from components."""
        # Use SQLite for development
        return "sqlite+aiosqlite:///./secrets_vault.db"

    # KMS Configuration
    kms_provider: str = "local"  # local, aws, azure, gcp
    kms_key_id: Optional[str] = None
    kms_region: Optional[str] = None

    # Local KMS settings (for development)
    master_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    encryption_algorithm: str = "AES-256-GCM"

    # AWS KMS settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"

    # Secret Storage Configuration
    secret_max_length: int = 64 * 1024  # 64KB
    secret_rotation_days: int = 90
    secret_access_log_retention_days: int = 365

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = True
    jaeger_endpoint: Optional[str] = None
    log_level: str = "INFO"

    # Rate Limiting
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst: int = 200

    # Environment
    environment: str = "development"
    debug: bool = False

    # Audit Configuration
    audit_enabled: bool = True
    audit_log_all_access: bool = True
    audit_retention_days: int = 2555  # 7 years

    # Namespace Configuration
    default_namespace: str = "default"
    namespace_separation_enabled: bool = True

    # Backup Configuration
    backup_enabled: bool = True
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    backup_retention_days: int = 30


# Global settings instance
settings = Settings()
