"""
Configuration management for compliance export service.
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost/compliance_db",
        env="DATABASE_URL",
        description="Database connection URL",
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis connection URL for Celery",
    )

    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_BROKER_URL",
        description="Celery broker URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        env="CELERY_RESULT_BACKEND",
        description="Celery result backend URL",
    )

    # Encryption Configuration
    compliance_master_key: Optional[str] = Field(
        default=None,
        env="COMPLIANCE_MASTER_KEY",
        description="Master encryption key for AES encryption",
    )

    # Export Configuration
    compliance_export_path: str = Field(
        default="/tmp/compliance-exports",
        env="COMPLIANCE_EXPORT_PATH",
        description="Base path for export files",
    )
    export_retention_days: int = Field(
        default=90,
        env="EXPORT_RETENTION_DAYS",
        description="Number of days to retain export files",
    )

    # Security Configuration
    secret_key: str = Field(
        default="compliance-export-secret-key-change-in-production",
        env="SECRET_KEY",
        description="Secret key for session management",
    )
    allowed_hosts: list[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS",
        description="Allowed hosts for CORS",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level",
    )
    log_format: str = Field(
        default="json",
        env="LOG_FORMAT",
        description="Log format (json, text)",
    )

    # API Configuration
    api_title: str = Field(
        default="Compliance Export Service",
        description="API title",
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version",
    )
    api_description: str = Field(
        default="State-format exports with audit logs and encryption at rest",
        description="API description",
    )

    # Performance Configuration
    max_export_file_size: int = Field(
        default=1024 * 1024 * 1024,  # 1GB
        env="MAX_EXPORT_FILE_SIZE",
        description="Maximum export file size in bytes",
    )
    export_batch_size: int = Field(
        default=10000,
        env="EXPORT_BATCH_SIZE",
        description="Batch size for export processing",
    )
    max_concurrent_exports: int = Field(
        default=5,
        env="MAX_CONCURRENT_EXPORTS",
        description="Maximum concurrent export jobs",
    )

    # Compliance Configuration
    audit_log_retention_years: int = Field(
        default=7,
        env="AUDIT_LOG_RETENTION_YEARS",
        description="Audit log retention period in years",
    )
    require_two_factor_auth: bool = Field(
        default=False,
        env="REQUIRE_TWO_FACTOR_AUTH",
        description="Require two-factor authentication",
    )

    # State-specific Configuration
    edfacts_api_endpoint: Optional[str] = Field(
        default=None,
        env="EDFACTS_API_ENDPOINT",
        description="EDFacts API endpoint",
    )
    calpads_sftp_host: Optional[str] = Field(
        default=None,
        env="CALPADS_SFTP_HOST",
        description="CALPADS SFTP host",
    )
    calpads_sftp_username: Optional[str] = Field(
        default=None,
        env="CALPADS_SFTP_USERNAME",
        description="CALPADS SFTP username",
    )
    calpads_sftp_private_key_path: Optional[str] = Field(
        default=None,
        env="CALPADS_SFTP_PRIVATE_KEY_PATH",
        description="CALPADS SFTP private key path",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class CeleryConfig:
    """Celery configuration."""

    def __init__(self, settings: Settings):
        """Initialize Celery configuration."""
        self.broker_url = settings.celery_broker_url
        self.result_backend = settings.celery_result_backend
        self.task_serializer = "json"
        self.accept_content = ["json"]
        self.result_serializer = "json"
        self.timezone = "UTC"
        self.enable_utc = True
        
        # Task routing
        self.task_routes = {
            "app.jobs.process_compliance_export": {"queue": "exports"},
            "app.jobs.validate_export_data": {"queue": "validation"},
            "app.jobs.cleanup_old_exports": {"queue": "maintenance"},
            "app.jobs.generate_compliance_report": {"queue": "reports"},
        }
        
        # Task retry configuration
        self.task_acks_late = True
        self.worker_prefetch_multiplier = 1
        self.task_default_max_retries = 3
        self.task_default_retry_delay = 60
        
        # Worker configuration
        self.worker_max_tasks_per_child = 1000
        self.worker_disable_rate_limits = False
        
        # Security
        self.worker_hijack_root_logger = False
        self.worker_log_color = False


class DatabaseConfig:
    """Database configuration."""

    def __init__(self, settings: Settings):
        """Initialize database configuration."""
        self.url = settings.database_url
        self.echo = settings.log_level.upper() == "DEBUG"
        self.pool_size = 10
        self.max_overflow = 20
        self.pool_timeout = 30
        self.pool_recycle = 3600
        self.pool_pre_ping = True


# Global settings instance
settings = Settings()

# Configuration instances
celery_config = CeleryConfig(settings)
database_config = DatabaseConfig(settings)
