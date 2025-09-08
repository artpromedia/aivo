"""Application configuration."""

import os
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service Information
    service_name: str = Field(
        default="slp-sel-svc", description="Service name"
    )
    service_version: str = Field(
        default="0.1.0", description="Service version"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")

    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:pass@localhost:5432/slp_sel_db",
        description="Database connection URL",
    )
    database_echo: bool = Field(
        default=False, description="Echo SQL queries"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )

    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for encryption",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )

    # Speech Processing Configuration
    sample_rate: int = Field(
        default=16000, description="Audio sample rate for processing"
    )
    max_audio_duration_seconds: int = Field(
        default=30, description="Maximum audio duration in seconds"
    )
    phoneme_confidence_threshold: float = Field(
        default=0.6, description="Minimum confidence for phoneme recognition"
    )

    # Articulation Scoring Configuration
    target_phonemes: list[str] = Field(
        default=[
            "p", "b", "t", "d", "k", "g", "f", "v", "θ", "ð",
            "s", "z", "ʃ", "ʒ", "tʃ", "dʒ", "m", "n", "ŋ",
            "l", "r", "w", "j", "h"
        ],
        description="Target phonemes for articulation assessment",
    )
    scoring_weights: dict[str, float] = Field(
        default={
            "accuracy": 0.4,
            "timing": 0.3,
            "consistency": 0.2,
            "fluency": 0.1,
        },
        description="Weights for articulation scoring components",
    )

    # SEL Journaling Configuration
    max_journal_entry_length: int = Field(
        default=5000, description="Maximum characters in journal entry"
    )
    journal_retention_days: int = Field(
        default=365, description="Journal retention period in days"
    )
    enable_sentiment_analysis: bool = Field(
        default=True,
        description="Enable sentiment analysis for journal entries",
    )

    # File Storage Configuration
    upload_max_size: int = Field(
        default=10 * 1024 * 1024, description="Maximum upload size in bytes"
    )
    allowed_audio_formats: list[str] = Field(
        default=["wav", "mp3", "m4a", "flac"],
        description="Allowed audio file formats",
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS"
    )
    cors_allow_methods: list[str] = Field(
        default=["*"], description="Allowed CORS methods"
    )
    cors_allow_headers: list[str] = Field(
        default=["*"], description="Allowed CORS headers"
    )

    # Performance Configuration
    connection_pool_size: int = Field(
        default=20, description="Database connection pool size"
    )
    connection_pool_overflow: int = Field(
        default=10, description="Database connection pool overflow"
    )
    request_timeout_seconds: int = Field(
        default=30, description="Request timeout in seconds"
    )

    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy."""
        return self.database_url

    def get_redis_url(self) -> str:
        """Get Redis URL."""
        return self.redis_url

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug or os.getenv("ENVIRONMENT", "").lower() in [
            "dev", "development", "local"
        ]

    def get_cors_config(self) -> dict[str, Any]:
        """Get CORS configuration."""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": self.cors_allow_credentials,
            "allow_methods": self.cors_allow_methods,
            "allow_headers": self.cors_allow_headers,
        }


# Global settings instance
settings = Settings()
