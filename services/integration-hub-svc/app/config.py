"""Configuration settings for the Integration Hub Service."""

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
    project_name: str = "Integration Hub Service"
    version: str = "0.1.0"
    description: str = "API Keys & Webhooks Management Service"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8300
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
    database_name: str = "integration_hub"
    database_pool_size: int = 10
    database_max_overflow: int = 20

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
    redis_db: int = 0
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

    # Celery Configuration
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    celery_task_routes: dict[str, str] = {
        "app.tasks.webhook_delivery": "webhooks",
        "app.tasks.webhook_retry": "webhooks",
    }

    @computed_field  # type: ignore[misc]
    @property
    def celery_broker(self) -> str:
        """Celery broker URL."""
        return self.celery_broker_url or str(self.redis_url)

    @computed_field  # type: ignore[misc]
    @property
    def celery_backend(self) -> str:
        """Celery result backend URL."""
        return self.celery_result_backend or str(self.redis_url)

    # API Keys Configuration
    api_key_length: int = 32
    api_key_prefix: str = "aivo_"
    api_key_ttl_days: int = 365

    # Webhook Configuration
    webhook_timeout_seconds: int = 30
    webhook_max_retries: int = 5
    webhook_initial_delay_seconds: int = 1
    webhook_max_delay_seconds: int = 300
    webhook_backoff_multiplier: float = 2.0
    webhook_signature_header: str = "X-Aivo-Signature"
    webhook_signature_algorithm: str = "sha256"

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

    # Feature Flags
    enable_webhook_replay: bool = True
    enable_api_key_rotation: bool = True
    enable_webhook_testing: bool = True

    # Rate Limiting
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst: int = 200

    # Environment
    environment: str = "development"
    debug: bool = False

    # External Services
    echo_site_url: str = "https://echo.site"
    health_check_timeout: int = 5


# Global settings instance
settings = Settings()
