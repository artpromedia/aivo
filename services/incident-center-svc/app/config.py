"""
Incident Center Service Configuration
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service configuration
    SERVICE_NAME: str = "incident-center-svc"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API configuration
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://incident_user:incident_pass@localhost/incident_db"
    DATABASE_ECHO: bool = False

    # Redis for caching and real-time
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Security
    SECRET_KEY: str = "incident-center-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Notification settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    FROM_EMAIL: str = "incidents@example.com"

    # Twilio for SMS
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_PHONE: Optional[str] = None

    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_CONNECTION_TIMEOUT: int = 300

    # External integrations
    STATUSPAGE_API_KEY: Optional[str] = None
    STATUSPAGE_PAGE_ID: Optional[str] = None
    STATUSPAGE_BASE_URL: str = "https://api.statuspage.io/v1"

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    # Monitoring
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30

    # Task queue (Celery)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Incident settings
    DEFAULT_INCIDENT_SEVERITY: str = "medium"
    INCIDENT_AUTO_RESOLVE_HOURS: int = 24
    BANNER_DEFAULT_DURATION_MINUTES: int = 60

    # Subscription limits
    MAX_SUBSCRIPTIONS_PER_TENANT: int = 100
    MAX_CHANNELS_PER_SUBSCRIPTION: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
