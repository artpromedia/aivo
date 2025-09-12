"""
Configuration settings for the ELA Evaluator service.

This module handles environment-based configuration for rubric scoring,
PII moderation, and content safety features.
"""

from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service configuration
    service_name: str = Field(default="ela-eval-svc", alias="SERVICE_NAME")
    service_version: str = Field(default="0.1.0", alias="SERVICE_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Server configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database configuration
    database_url: str = Field(
        default="postgresql://user:pass@localhost:5432/ela_eval",
        alias="DATABASE_URL",
    )

    # Redis configuration for caching
    redis_url: str = Field(
        default="redis://localhost:6379/0", alias="REDIS_URL"
    )

    # AI Model configuration
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    default_model: str = Field(
        default="gpt-4-turbo-preview", alias="DEFAULT_MODEL"
    )

    # Rubric scoring configuration
    max_submission_length: int = Field(
        default=10000, alias="MAX_SUBMISSION_LENGTH"
    )
    scoring_timeout_seconds: int = Field(
        default=30, alias="SCORING_TIMEOUT_SECONDS"
    )
    enable_rubric_caching: bool = Field(
        default=True, alias="ENABLE_RUBRIC_CACHING"
    )

    # PII and content moderation
    enable_pii_detection: bool = Field(
        default=True, alias="ENABLE_PII_DETECTION"
    )
    enable_content_moderation: bool = Field(
        default=True, alias="ENABLE_CONTENT_MODERATION"
    )
    pii_confidence_threshold: float = Field(
        default=0.8, alias="PII_CONFIDENCE_THRESHOLD"
    )

    # Grade band configuration
    supported_grade_bands: list[str] = Field(
        default=["K-2", "3-5", "6-8", "9-12"], alias="SUPPORTED_GRADE_BANDS"
    )

    @property
    def database_echo(self: Self) -> bool:
        """Enable SQLAlchemy query logging in debug mode."""
        return self.debug

    @property
    def cors_origins(self: Self) -> list[str]:
        """Get CORS origins based on environment."""
        if self.debug:
            return ["*"]
        return [
            "https://app.aivo.com",
            "https://admin.aivo.com",
            "https://teacher.aivo.com",
        ]


settings = Settings()
