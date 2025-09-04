"""Configuration settings for coursework ingest service."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Basic service settings
    service_name: str = "coursework-ingest-svc"
    version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Host to bind")
    port: int = Field(default=8004, description="Port to bind")

    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./coursework_ingest.db",
        description="Database connection URL",
    )

    # AWS/S3 settings
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = Field(default="us-east-1")
    s3_bucket: str = Field(default="aivo-coursework-uploads")
    s3_endpoint_url: str | None = None

    # Redis settings for async processing
    redis_url: str = Field(default="redis://localhost:6379/0")

    # OpenAI settings for topic extraction
    openai_api_key: str | None = None
    openai_model: str = Field(default="gpt-4o-mini")

    # Content moderation settings
    moderation_threshold: float = Field(
        default=0.85,
        description="Minimum confidence for content approval",
    )

    # OCR settings
    tesseract_path: str | None = None
    poppler_path: str | None = None

    # File upload settings
    max_file_size: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="Maximum file size in bytes",
    )
    allowed_extensions: list[str] = Field(
        default=[".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"],
        description="Allowed file extensions",
    )

    # PII detection settings
    pii_entities: list[str] = Field(
        default=[
            "PERSON",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
            "CREDIT_CARD",
            "SSN",
            "US_PASSPORT",
            "US_DRIVER_LICENSE",
        ],
        description="PII entities to detect and mask",
    )

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)


settings = Settings()
