"""Model Dispatch Policy Service - Configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Service configuration
    service_name: str = Field(default="model-dispatch-svc", description="Service name")
    service_version: str = Field(default="0.1.0", description="Service version")
    host: str = Field(default="0.0.0.0", description="Host to bind the server")
    port: int = Field(default=8004, description="Port to bind the server")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Cache configuration
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    cache_redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    cache_ttl_seconds: int = Field(default=3600, description="Default cache TTL in seconds")

    # Policy configuration
    config_file_path: str = Field(
        default="config/policy_rules.yaml",
        description="Path to policy configuration file",
    )
    auto_reload_config: bool = Field(default=True, description="Auto-reload configuration changes")
    config_check_interval_seconds: int = Field(
        default=60, description="Configuration check interval"
    )

    # Provider defaults
    default_provider: str = Field(default="openai", description="Default LLM provider")
    default_moderation_threshold: float = Field(
        default=0.7, description="Default content moderation threshold"
    )

    # Regional routing
    enforce_data_residency: bool = Field(
        default=True, description="Enforce data residency requirements"
    )
    fallback_to_local: bool = Field(
        default=True,
        description="Fallback to local models if region unavailable",
    )

    # Teacher overrides
    max_override_duration_hours: int = Field(
        default=168, description="Maximum override duration (1 week)"
    )
    override_cache_ttl_seconds: int = Field(default=3600, description="Teacher override cache TTL")

    # Performance settings
    max_concurrent_requests: int = Field(
        default=100, description="Maximum concurrent policy requests"
    )
    request_timeout_seconds: int = Field(default=30, description="Request timeout in seconds")

    # Monitoring and logging
    log_level: str = Field(default="INFO", description="Logging level")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9004, description="Metrics server port")

    # CORS settings
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods",
    )
    cors_headers: list[str] = Field(default=["*"], description="Allowed CORS headers")


# Global settings instance
settings = Settings()
