"""
Configuration settings for the Approval Service.
"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server configuration
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8080, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database configuration
    database_url: str = Field(
        default="postgresql+asyncpg://approval:approval@localhost:5432/approval_db",
        description="Database connection URL"
    )
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database max overflow connections")
    
    # Redis configuration for caching and task queue
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    redis_ttl: int = Field(default=3600, description="Default Redis TTL in seconds")
    
    # Celery configuration for background tasks
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", 
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", 
        description="Celery result backend URL"
    )
    
    # Approval workflow settings
    default_ttl_hours: int = Field(default=72, description="Default approval TTL in hours")
    max_ttl_hours: int = Field(default=720, description="Maximum approval TTL in hours")  # 30 days
    min_ttl_hours: int = Field(default=1, description="Minimum approval TTL in hours")
    
    reminder_hours_before_expiry: List[int] = Field(
        default=[24, 12, 6, 1], 
        description="Hours before expiry to send reminders"
    )
    
    # Webhook configuration
    webhook_timeout: float = Field(default=30.0, description="Webhook request timeout")
    webhook_retry_attempts: int = Field(default=3, description="Webhook retry attempts")
    webhook_retry_delay: float = Field(default=60.0, description="Webhook retry delay in seconds")
    
    # Security settings
    jwt_secret_key: str = Field(default="your-secret-key", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration hours")
    
    # API settings
    api_version: str = Field(default="v1", description="API version")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )
    
    # Tenant configuration
    multi_tenant: bool = Field(default=True, description="Enable multi-tenant support")
    default_tenant_id: str = Field(default="default", description="Default tenant ID")
    
    # Notification settings
    notification_service_url: Optional[str] = Field(
        default="http://localhost:8090/notifications",
        description="Notification service URL"
    )
    
    # External service URLs
    user_service_url: Optional[str] = Field(
        default="http://localhost:8070/users",
        description="User service URL for participant validation"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
