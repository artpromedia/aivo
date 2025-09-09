"""Application configuration for Device Policy Service."""


from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/device_policy_db"
    sql_debug: bool = False

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]

    # Security
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30

    # Policy sync
    long_poll_timeout: int = 300
    max_sync_attempts: int = 5

    # Allowlist
    default_allowlist_priority: int = 100
    max_allowlist_entries: int = 10000

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_prefix = "DEVICE_POLICY_"


# Global settings instance
settings = Settings()
