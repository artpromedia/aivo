"""Configuration settings for Problem Session Orchestrator."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Service Configuration
    service_name: str = Field(
        default="problem-session-svc",
        description="Service name for identification"
    )
    host: str = Field(default="127.0.0.1", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(
        default="INFO", description="Logging level"
    )

    # External Service URLs
    ink_service_url: str = Field(
        default="http://localhost:8001",
        description="URL for ink capture service"
    )
    math_service_url: str = Field(
        default="http://localhost:8002",
        description="URL for math recognition service"
    )
    science_service_url: str = Field(
        default="http://localhost:8003",
        description="URL for science solver service"
    )
    subject_brain_url: str = Field(
        default="http://localhost:8004",
        description="URL for subject brain service"
    )
    event_service_url: str = Field(
        default="http://localhost:8080/events",
        description="URL for event publishing service"
    )

    # Session Configuration
    session_timeout_minutes: int = Field(
        default=30, description="Default session timeout in minutes"
    )
    max_session_duration_minutes: int = Field(
        default=120, description="Maximum session duration in minutes"
    )
    default_canvas_width: int = Field(
        default=800, description="Default canvas width"
    )
    default_canvas_height: int = Field(
        default=600, description="Default canvas height"
    )

    # Recognition Configuration
    recognition_confidence_threshold: float = Field(
        default=0.7, description="Minimum confidence for recognition"
    )
    recognition_timeout_seconds: int = Field(
        default=30, description="Recognition timeout in seconds"
    )

    # Event Configuration
    enable_events: bool = Field(
        default=True, description="Enable event publishing"
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/"
                "problem_session_db",
        description="Database connection URL"
    )


# Global settings instance
settings = Settings()
