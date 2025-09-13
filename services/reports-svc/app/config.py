"""Configuration settings for the reports service."""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/reports_db"
    )

    # ClickHouse
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", "9000"))
    clickhouse_user: str = os.getenv("CLICKHOUSE_USER", "default")
    clickhouse_password: str = os.getenv("CLICKHOUSE_PASSWORD", "")
    clickhouse_database: str = os.getenv("CLICKHOUSE_DATABASE", "aivo_analytics")

    # Redis (for background tasks)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # S3 Storage
    s3_bucket: str = os.getenv("S3_BUCKET", "aivo-reports")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")

    # Local storage (fallback)
    local_storage_path: str = os.getenv("LOCAL_STORAGE_PATH", "/app/exports")

    # Email settings
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "reports@aivo.com")

    # Security
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # Export settings
    max_row_limit: int = int(os.getenv("MAX_ROW_LIMIT", "100000"))
    export_timeout_seconds: int = int(os.getenv("EXPORT_TIMEOUT_SECONDS", "300"))
    download_url_expire_hours: int = int(os.getenv("DOWNLOAD_URL_EXPIRE_HOURS", "24"))

    # Service settings
    service_name: str = "reports-svc"
    service_version: str = "1.0.0"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
