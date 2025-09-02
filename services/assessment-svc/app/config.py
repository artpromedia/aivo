"""
Configuration settings for the Assessment service.
"""
import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Assessment Configuration
    default_subject: str = Field(
        default="mathematics", 
        description="Default subject for assessment"
    )
    min_questions: int = Field(
        default=5, 
        description="Minimum questions for assessment",
        ge=3,
        le=10
    )
    max_questions: int = Field(
        default=7, 
        description="Maximum questions for assessment",
        ge=5,
        le=15
    )
    convergence_threshold: float = Field(
        default=0.8, 
        description="Confidence threshold for level convergence",
        ge=0.5,
        le=1.0
    )
    
    # Event Publishing
    event_endpoint: str = Field(
        default="http://localhost:8080/events", 
        description="Event publishing endpoint"
    )
    event_timeout: int = Field(
        default=10, 
        description="Event publishing timeout in seconds",
        ge=1,
        le=60
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
