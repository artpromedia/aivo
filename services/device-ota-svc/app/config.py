"""Configuration settings for Device OTA & Heartbeat Service."""

from functools import lru_cache
from typing import Any

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Environment
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/device_ota",
        description="Database connection URL",
    )
    database_pool_size: int = Field(default=10, description="Database pool size")
    database_pool_overflow: int = Field(default=20, description="Database pool overflow")

    # Security
    secret_key: str = Field(
        default="device-ota-secret-key-change-in-production",
        description="Secret key for signing tokens",
    )
    allowed_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1", "*.example.com"],
        description="Allowed hosts",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins",
    )

    # File Storage
    storage_type: str = Field(default="local", description="Storage backend type")
    storage_base_path: str = Field(
        default="./storage/firmware",
        description="Base path for firmware storage",
    )
    storage_s3_bucket: str | None = Field(None, description="S3 bucket name")
    storage_s3_region: str | None = Field(None, description="S3 region")
    storage_s3_access_key: str | None = Field(None, description="S3 access key")
    storage_s3_secret_key: str | None = Field(None, description="S3 secret key")

    # Update Configuration
    max_concurrent_downloads: int = Field(
        default=100, description="Maximum concurrent downloads per update"
    )
    max_file_size_mb: int = Field(default=1024, description="Maximum firmware file size in MB")
    update_timeout_hours: int = Field(default=24, description="Update timeout in hours")
    heartbeat_timeout_minutes: int = Field(default=30, description="Heartbeat timeout in minutes")

    # Deployment Rings
    canary_max_devices: int = Field(default=50, description="Maximum devices in canary ring")
    early_max_devices: int = Field(default=500, description="Maximum devices in early ring")

    # Rollback Configuration
    auto_rollback_failure_threshold: float = Field(
        default=10.0, description="Auto rollback failure rate threshold"
    )
    rollback_timeout_hours: int = Field(default=6, description="Rollback timeout in hours")

    # Monitoring
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    health_check_timeout: int = Field(default=30, description="Health check timeout")

    # External Services
    notification_service_url: str | None = Field(None, description="Notification service URL")
    analytics_service_url: str | None = Field(None, description="Analytics service URL")

    # Rate Limiting
    rate_limit_heartbeat: str = Field(default="100/minute", description="Heartbeat rate limit")
    rate_limit_update_check: str = Field(default="10/minute", description="Update check rate limit")

    @validator("log_level")
    @classmethod
    def validate_log_level(cls: type["Settings"], v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("storage_type")
    @classmethod
    def validate_storage_type(cls: type["Settings"], v: str) -> str:
        """Validate storage type."""
        valid_types = ["local", "s3"]
        if v not in valid_types:
            raise ValueError(f"Storage type must be one of: {valid_types}")
        return v

    @validator("environment")
    @classmethod
    def validate_environment(cls: type["Settings"], v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v

    @validator("auto_rollback_failure_threshold")
    @classmethod
    def validate_failure_threshold(cls: type["Settings"], v: float) -> float:
        """Validate failure threshold."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("Failure threshold must be between 0 and 100")
        return v

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_prefix = "DEVICE_OTA_"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_database_url() -> str:
    """Get database URL from settings."""
    settings = get_settings()
    return settings.database_url


def get_storage_config() -> dict[str, Any]:
    """Get storage configuration."""
    settings = get_settings()

    config = {
        "type": settings.storage_type,
        "base_path": settings.storage_base_path,
    }

    if settings.storage_type == "s3":
        config.update(
            {
                "bucket": settings.storage_s3_bucket,
                "region": settings.storage_s3_region,
                "access_key": settings.storage_s3_access_key,
                "secret_key": settings.storage_s3_secret_key,
            }
        )

    return config
