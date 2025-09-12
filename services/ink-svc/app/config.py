"""
Configuration settings for the ink capture service.

This module handles environment-based configuration for the digital ink
capture service, including database settings, S3 storage, and event
publishing configurations.
"""

from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application settings
    app_name: str = Field(default="Ink Capture Service", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ink_db", alias="DATABASE_URL"
    )

    # AWS S3 settings for ink storage
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket_name: str = Field(default="aivo-ink-storage", alias="S3_BUCKET_NAME")
    s3_prefix: str = Field(default="ink-pages", alias="S3_PREFIX")

    # Event publishing settings
    event_service_url: str = Field(
        default="http://localhost:8080/events", alias="EVENT_SERVICE_URL"
    )
    enable_events: bool = Field(default=True, alias="ENABLE_EVENTS")

    # Security and validation
    max_strokes_per_request: int = Field(default=1000, alias="MAX_STROKES_PER_REQUEST")
    max_points_per_stroke: int = Field(default=10000, alias="MAX_POINTS_PER_STROKE")
    session_timeout_minutes: int = Field(default=60, alias="SESSION_TIMEOUT_MINUTES")

    # Content moderation
    enable_consent_gate: bool = Field(default=True, alias="ENABLE_CONSENT_GATE")
    enable_media_gate: bool = Field(default=True, alias="ENABLE_MEDIA_GATE")

    @property
    def s3_key_prefix(self: Self) -> str:
        """Generate S3 key prefix for ink storage."""
        return f"{self.s3_prefix}/"


settings = Settings()
