"""Configuration settings for roster sync service."""

from typing import Any

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""

    # Service configuration
    service_name: str = Field(default="roster-sync-service", env="SERVICE_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Database configuration
    database_url: str = Field(
        default="postgresql+asyncpg://user:pass@localhost/roster_sync",
        env="DATABASE_URL",
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_pool_overflow: int = Field(default=30, env="DATABASE_POOL_OVERFLOW")

    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")

    # Celery configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", env="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND"
    )
    celery_worker_concurrency: int = Field(default=4, env="CELERY_WORKER_CONCURRENCY")

    # API configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=1, env="API_WORKERS")

    # Security configuration
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    encryption_key: str = Field(default="dev-encryption-key", env="ENCRYPTION_KEY")

    # Webhook configuration
    webhook_timeout: int = Field(default=30, env="WEBHOOK_TIMEOUT")
    webhook_max_retries: int = Field(default=3, env="WEBHOOK_MAX_RETRIES")

    # OneRoster configuration defaults
    oneroster_timeout: int = Field(default=30, env="ONEROSTER_TIMEOUT")
    oneroster_rate_limit: float = Field(default=0.5, env="ONEROSTER_RATE_LIMIT")
    oneroster_max_retries: int = Field(default=3, env="ONEROSTER_MAX_RETRIES")

    # Clever configuration defaults
    clever_timeout: int = Field(default=30, env="CLEVER_TIMEOUT")
    clever_rate_limit: float = Field(default=0.2, env="CLEVER_RATE_LIMIT")
    clever_max_retries: int = Field(default=3, env="CLEVER_MAX_RETRIES")

    # CSV processing configuration
    csv_max_file_size: int = Field(
        default=100 * 1024 * 1024, env="CSV_MAX_FILE_SIZE"
    )  # 100MB
    csv_encoding_detection: bool = Field(default=True, env="CSV_ENCODING_DETECTION")
    csv_chunk_size: int = Field(default=1000, env="CSV_CHUNK_SIZE")

    # SCIM configuration
    scim_timeout: int = Field(default=30, env="SCIM_TIMEOUT")
    scim_max_retries: int = Field(default=3, env="SCIM_MAX_RETRIES")
    scim_batch_size: int = Field(default=100, env="SCIM_BATCH_SIZE")

    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )

    # Monitoring configuration
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    # Job configuration
    job_timeout: int = Field(default=3600, env="JOB_TIMEOUT")  # 1 hour
    job_soft_timeout: int = Field(default=3300, env="JOB_SOFT_TIMEOUT")  # 55 minutes
    job_max_records: int = Field(default=1000000, env="JOB_MAX_RECORDS")  # 1M records

    # Cleanup configuration
    cleanup_job_age_days: int = Field(default=30, env="CLEANUP_JOB_AGE_DAYS")
    cleanup_log_age_days: int = Field(default=7, env="CLEANUP_LOG_AGE_DAYS")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_database_config(self) -> dict[str, Any]:
        """Get database configuration."""
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "pool_overflow": self.database_pool_overflow,
            "echo": self.debug,
        }

    def get_celery_config(self) -> dict[str, Any]:
        """Get Celery configuration."""
        return {
            "broker_url": self.celery_broker_url,
            "result_backend": self.celery_result_backend,
            "worker_concurrency": self.celery_worker_concurrency,
            "task_serializer": "json",
            "accept_content": ["json"],
            "result_serializer": "json",
            "timezone": "UTC",
            "enable_utc": True,
            "task_track_started": True,
            "task_time_limit": self.job_timeout,
            "task_soft_time_limit": self.job_soft_timeout,
            "worker_prefetch_multiplier": 1,
            "worker_max_tasks_per_child": 50,
        }

    def get_connector_defaults(self, connector_type: str) -> dict[str, Any]:
        """Get default configuration for a connector type."""
        defaults = {
            "oneroster": {
                "timeout": self.oneroster_timeout,
                "rate_limit_delay": self.oneroster_rate_limit,
                "max_retries": self.oneroster_max_retries,
                "page_size": 100,
                "filter_active_only": True,
                "include_deleted": False,
            },
            "clever": {
                "timeout": self.clever_timeout,
                "rate_limit_delay": self.clever_rate_limit,
                "max_retries": self.clever_max_retries,
                "page_size": 1000,
                "filter_active_only": True,
                "include_deleted": False,
            },
            "csv": {
                "max_file_size": self.csv_max_file_size,
                "encoding_detection": self.csv_encoding_detection,
                "chunk_size": self.csv_chunk_size,
                "validate_headers": True,
                "skip_empty_rows": True,
            },
        }

        return defaults.get(connector_type, {})


# Global settings instance
settings = Settings()


# Environment-specific configurations
def get_settings() -> Settings:
    """Get application settings."""
    return settings


def configure_logging() -> None:
    """Configure application logging."""
    import logging

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()), format=settings.log_format
    )

    # Set specific logger levels
    if settings.debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("celery").setLevel(logging.DEBUG)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("celery").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
