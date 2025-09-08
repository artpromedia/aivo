"""
Configuration settings for the Inference Gateway service.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API base URL"
    )
    default_model: str = Field(default="gpt-3.5-turbo", description="Default generation model")
    default_embedding_model: str = Field(
        default="text-embedding-ada-002", description="Default embedding model"
    )

    # Moderation Configuration
    moderation_threshold: float = Field(
        default=0.85, description="Content moderation threshold", ge=0.0, le=1.0
    )
    moderation_model: str = Field(
        default="text-moderation-latest", description="OpenAI moderation model"
    )

    # PII Configuration
    pii_detection_enabled: bool = Field(default=True, description="Enable PII detection")
    pii_anonymization_enabled: bool = Field(default=True, description="Enable PII anonymization")
    supported_languages: list[str] = Field(
        default=["en"], description="Supported languages for PII detection"
    )

    # Rate Limiting
    max_tokens_per_request: int = Field(default=4096, description="Maximum tokens per request")
    max_requests_per_minute: int = Field(default=60, description="Maximum requests per minute")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
