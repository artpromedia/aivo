"""
Configuration settings for the Notification Service.
"""
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # App settings
    app_name: str = Field(default="Notification Service", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8090, description="Server port")
    
    # Email settings
    smtp_server: Optional[str] = Field(default=None, description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    
    # Email defaults
    from_email: str = Field(default="noreply@aivo.edu", description="Default from email")
    from_name: str = Field(default="Aivo Education Platform", description="Default from name")
    
    # Development settings
    dev_mode: bool = Field(default=True, description="Development mode - don't send real emails")
    dev_email_dump_path: str = Field(
        default="./dev_emails", 
        description="Path to dump development emails"
    )
    
    # Template settings
    templates_path: str = Field(default="./templates", description="Path to email templates")
    
    # Security
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    allowed_origins: List[str] = Field(
        default=["*"], 
        description="CORS allowed origins"
    )
    
    # Notification limits
    max_recipients_per_request: int = Field(
        default=100, 
        description="Maximum recipients per notification request"
    )
    rate_limit_per_minute: int = Field(
        default=60, 
        description="Rate limit per minute"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="NOTIFICATION_"
    )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Global settings instance
settings = Settings()
