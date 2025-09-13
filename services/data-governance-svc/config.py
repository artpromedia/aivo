"""
Configuration settings for Data Governance Service
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8084
    DEBUG: bool = False

    # Database configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/aivo_governance"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File storage
    EXPORT_STORAGE_PATH: str = "/tmp/dsr_exports"
    EXPORT_MAX_SIZE_MB: int = 100
    EXPORT_TTL_HOURS: int = 72  # How long export files are kept

    # Background job configuration
    CLEANUP_INTERVAL_MINUTES: int = 60
    RETENTION_CHECK_INTERVAL_HOURS: int = 24

    # External services
    NOTIFICATION_SERVICE_URL: Optional[str] = None
    AUDIT_SERVICE_URL: Optional[str] = None

    # Compliance settings
    DEFAULT_RETENTION_DAYS: int = 2555  # 7 years default
    LEGAL_HOLD_NOTIFICATION_EMAILS: List[str] = []

    # FERPA/COPPA specific
    MINOR_AGE_THRESHOLD: int = 13  # COPPA threshold
    EDUCATIONAL_RECORD_RETENTION_YEARS: int = 5  # FERPA guideline

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
