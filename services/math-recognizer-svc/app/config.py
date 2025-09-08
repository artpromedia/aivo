"""Configuration for Math Recognizer Service."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service configuration
    service_name: str = Field(default="math-recognizer-svc")
    service_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)

    # Server configuration
    host: str = Field(default="127.0.0.1")  # Bind to localhost for security
    port: int = Field(default=8000)

    # Math recognition configuration
    confidence_threshold: float = Field(default=0.7)
    max_recognition_time: int = Field(default=30)  # seconds

    # CAS configuration
    cas_provider: str = Field(default="sympy")  # sympy, mathematica, etc.
    enable_step_by_step: bool = Field(default=True)

    # External services
    ink_service_url: str = Field(default="http://localhost:8001")

    # Logging
    log_level: str = Field(default="INFO")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
