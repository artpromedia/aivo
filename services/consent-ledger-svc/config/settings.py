"""
Configuration settings for consent ledger service.

Environment-based configuration with Pydantic validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Main application settings."""

    # Application
    APP_NAME: str = "Consent & Preferences Ledger"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://consent_user:consent_pass@localhost:5432/consent_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_DECODE_RESPONSES: bool = True

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Data Export
    EXPORT_STORAGE_PATH: str = "/tmp/consent_exports"
    EXPORT_MAX_FILE_SIZE_MB: int = 500
    EXPORT_RETENTION_DAYS: int = 30
    EXPORT_DEADLINE_DAYS: int = 10  # GDPR requirement

    # Data Deletion
    DELETION_VERIFICATION_DELAY_HOURS: int = 24
    DELETION_RETRY_MAX_ATTEMPTS: int = 3
    DELETION_RETENTION_YEARS: int = 7  # Legal requirement

    # Audit
    AUDIT_LOG_RETENTION_YEARS: int = 7
    AUDIT_INTEGRITY_CHECK_ENABLED: bool = True
    AUDIT_LOG_ENCRYPTION_ENABLED: bool = True

    # Email (for notifications)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = "noreply@district.edu"

    # Parental Consent
    PARENTAL_VERIFICATION_TOKEN_EXPIRY_HOURS: int = 72  # 3 days
    PARENTAL_RIGHTS_EXPIRY_DAYS: int = 365  # 1 year
    COPPA_AGE_THRESHOLD: int = 13

    # External Services
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET_PREFIX: str = "consent-ledger"

    MONGODB_URL: str | None = None
    MONGODB_DATABASE: str = "consent_data"

    SNOWFLAKE_ACCOUNT: str | None = None
    SNOWFLAKE_USER: str | None = None
    SNOWFLAKE_PASSWORD: str | None = None
    SNOWFLAKE_DATABASE: str | None = None
    SNOWFLAKE_SCHEMA: str | None = None
    SNOWFLAKE_WAREHOUSE: str | None = None

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 10

    # Monitoring
    SENTRY_DSN: str | None = None
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_ENABLED: bool = True

    @validator("EXPORT_STORAGE_PATH")
    def validate_export_path(self, v):
        """Ensure export storage path exists."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    @validator("LOG_LEVEL")
    def validate_log_level(self, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v.upper()

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(self, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


class DatabaseConfig:
    """Database configuration helper."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def connection_params(self) -> dict[str, Any]:
        """Get database connection parameters."""
        return {
            "pool_size": self.settings.DATABASE_POOL_SIZE,
            "max_overflow": self.settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": self.settings.DATABASE_POOL_TIMEOUT,
            "echo": self.settings.DATABASE_ECHO,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
        }


class CeleryConfig:
    """Celery configuration helper."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def config_dict(self) -> dict[str, Any]:
        """Get Celery configuration dictionary."""
        return {
            "broker_url": self.settings.CELERY_BROKER_URL,
            "result_backend": self.settings.CELERY_RESULT_BACKEND,
            "task_serializer": "json",
            "accept_content": ["json"],
            "result_serializer": "json",
            "timezone": "UTC",
            "enable_utc": True,
            "task_track_started": True,
            "task_time_limit": 30 * 60,  # 30 minutes
            "task_soft_time_limit": 25 * 60,  # 25 minutes
            "worker_prefetch_multiplier": 1,
            "task_acks_late": True,
            "worker_max_tasks_per_child": 1000,
            "task_always_eager": self.settings.CELERY_TASK_ALWAYS_EAGER,
            "task_routes": {
                "app.tasks.process_data_export": {"queue": "exports"},
                "app.tasks.process_data_deletion": {"queue": "deletions"},
                "app.tasks.cleanup_expired_exports": {"queue": "maintenance"},
                "app.tasks.verify_deletion_completion": {"queue": "verification"},
            },
            "beat_schedule": {
                "cleanup-expired-exports": {
                    "task": "app.tasks.cleanup_expired_exports",
                    "schedule": 86400.0,  # Daily
                },
                "check-overdue-exports": {
                    "task": "app.tasks.check_overdue_exports",
                    "schedule": 3600.0,  # Hourly
                },
            },
        }


class ExternalServicesConfig:
    """External services configuration helper."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def aws_config(self) -> dict[str, Any] | None:
        """Get AWS configuration if available."""
        if not self.settings.AWS_ACCESS_KEY_ID:
            return None

        return {
            "aws_access_key_id": self.settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": self.settings.AWS_SECRET_ACCESS_KEY,
            "region_name": self.settings.AWS_REGION,
        }

    @property
    def mongodb_config(self) -> dict[str, Any] | None:
        """Get MongoDB configuration if available."""
        if not self.settings.MONGODB_URL:
            return None

        return {
            "host": self.settings.MONGODB_URL,
            "server_selection_timeout_ms": 5000,
            "connect_timeout_ms": 5000,
            "socket_timeout_ms": 5000,
        }

    @property
    def snowflake_config(self) -> dict[str, Any] | None:
        """Get Snowflake configuration if available."""
        if not all(
            [
                self.settings.SNOWFLAKE_ACCOUNT,
                self.settings.SNOWFLAKE_USER,
                self.settings.SNOWFLAKE_PASSWORD,
            ]
        ):
            return None

        return {
            "account": self.settings.SNOWFLAKE_ACCOUNT,
            "user": self.settings.SNOWFLAKE_USER,
            "password": self.settings.SNOWFLAKE_PASSWORD,
            "database": self.settings.SNOWFLAKE_DATABASE,
            "schema": self.settings.SNOWFLAKE_SCHEMA,
            "warehouse": self.settings.SNOWFLAKE_WAREHOUSE,
            "client_session_keep_alive": True,
        }

    @property
    def smtp_config(self) -> dict[str, Any] | None:
        """Get SMTP configuration if available."""
        if not self.settings.SMTP_HOST:
            return None

        return {
            "hostname": self.settings.SMTP_HOST,
            "port": self.settings.SMTP_PORT,
            "username": self.settings.SMTP_USERNAME,
            "password": self.settings.SMTP_PASSWORD,
            "use_tls": self.settings.SMTP_USE_TLS,
            "from_email": self.settings.SMTP_FROM_EMAIL,
        }


class ComplianceConfig:
    """Compliance and privacy configuration helper."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def gdpr_settings(self) -> dict[str, Any]:
        """Get GDPR compliance settings."""
        return {
            "export_deadline_days": self.settings.EXPORT_DEADLINE_DAYS,
            "data_retention_years": self.settings.DELETION_RETENTION_YEARS,
            "audit_retention_years": self.settings.AUDIT_LOG_RETENTION_YEARS,
            "right_to_portability_enabled": True,
            "right_to_erasure_enabled": True,
            "consent_withdrawal_enabled": True,
        }

    @property
    def coppa_settings(self) -> dict[str, Any]:
        """Get COPPA compliance settings."""
        return {
            "age_threshold": self.settings.COPPA_AGE_THRESHOLD,
            "parental_verification_required": True,
            "parental_verification_expiry_hours": self.settings.PARENTAL_VERIFICATION_TOKEN_EXPIRY_HOURS,
            "parental_rights_expiry_days": self.settings.PARENTAL_RIGHTS_EXPIRY_DAYS,
            "verifiable_parental_consent_required": True,
        }

    @property
    def audit_settings(self) -> dict[str, Any]:
        """Get audit and logging settings."""
        return {
            "retention_years": self.settings.AUDIT_LOG_RETENTION_YEARS,
            "integrity_check_enabled": self.settings.AUDIT_INTEGRITY_CHECK_ENABLED,
            "encryption_enabled": self.settings.AUDIT_LOG_ENCRYPTION_ENABLED,
            "tamper_detection_enabled": True,
            "immutable_logs": True,
        }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return DatabaseConfig(get_settings())


def get_celery_config() -> CeleryConfig:
    """Get Celery configuration."""
    return CeleryConfig(get_settings())


def get_external_services_config() -> ExternalServicesConfig:
    """Get external services configuration."""
    return ExternalServicesConfig(get_settings())


def get_compliance_config() -> ComplianceConfig:
    """Get compliance configuration."""
    return ComplianceConfig(get_settings())
