"""
Configuration settings for the Admin Portal Aggregator Service.
"""
from typing import Optional, List, Dict
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App settings
    app_name: str = Field(default="Admin Portal Aggregator Service", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8095, description="Server port")
    
    # Service URLs
    tenant_service_url: str = Field(default="http://localhost:8080", description="Tenant service URL")
    payment_service_url: str = Field(default="http://localhost:8085", description="Payment service URL")
    approval_service_url: str = Field(default="http://localhost:8089", description="Approval service URL")
    analytics_service_url: str = Field(default="http://localhost:8096", description="Analytics service URL")
    fm_orchestrator_url: str = Field(default="http://localhost:8097", description="Private FM Orchestrator URL")
    
    # Cache settings
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL for caching")
    cache_ttl: int = Field(default=30, description="Cache TTL in seconds")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    
    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = Field(default=5, description="Circuit breaker failure threshold")
    circuit_breaker_recovery_timeout: int = Field(default=60, description="Circuit breaker recovery timeout")
    circuit_breaker_expected_exception: str = Field(default="httpx.RequestError", description="Expected exception for circuit breaker")
    
    # HTTP client settings
    http_timeout: float = Field(default=10.0, description="HTTP request timeout")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    
    # Security
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    allowed_origins: List[str] = Field(
        default=["*"], 
        description="CORS allowed origins"
    )
    
    # OpenTelemetry settings
    otel_service_name: str = Field(default="admin-portal-svc", description="OpenTelemetry service name")
    otel_exporter_endpoint: Optional[str] = Field(default=None, description="OpenTelemetry exporter endpoint")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per minute per tenant")
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="ADMIN_PORTAL_"
    )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
