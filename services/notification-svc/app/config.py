"""Configuration for notification service."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration."""

    # WebSocket
    WEBSOCKET_HOST: str = "0.0.0.0"
    WEBSOCKET_PORT: int = 8000

    # JWT
    JWT_SECRET: str = Field("dev-secret-key-change-in-production", env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Push Notifications
    VAPID_EMAIL: str = Field("admin@example.com", env="VAPID_EMAIL")
    VAPID_PUBLIC_KEY: str | None = Field(None, env="VAPID_PUBLIC_KEY")
    VAPID_PRIVATE_KEY: str | None = Field(None, env="VAPID_PRIVATE_KEY")

    # SMS
    SMS_PROVIDER: str = Field("twilio", env="SMS_PROVIDER")
    TWILIO_ACCOUNT_SID: str | None = Field(None, env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = Field(None, env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str | None = Field(
        None,
        env="TWILIO_PHONE_NUMBER",
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(
        ["http://localhost:3000"],
        env="CORS_ORIGINS",
    )

    # Logging
    LOG_LEVEL: str = "INFO"

    # Development
    DEVELOPMENT_MODE: bool = Field(False, env="DEVELOPMENT_MODE")

    class Config:
        """Pydantic configuration class."""

        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


settings = Settings()
