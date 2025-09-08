"""Configuration for Science Solver Service."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service configuration
    service_name: str = Field(default="science-solver-svc")
    service_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)

    # Server configuration
    host: str = Field(default="127.0.0.1")  # Bind to localhost for security
    port: int = Field(default=8000)

    # Science processing configuration
    max_equation_length: int = Field(default=1000)
    max_diagram_size_mb: int = Field(default=10)
    diagram_bbox_confidence: float = Field(default=0.7)

    # Unit validation configuration
    supported_unit_systems: list[str] = Field(
        default=["SI", "Imperial", "CGS", "US"],
    )
    enable_unit_conversion: bool = Field(default=True)

    # Chemistry configuration
    max_compounds_in_equation: int = Field(default=20)
    enable_redox_balancing: bool = Field(default=True)

    # External services
    diagram_service_url: str = Field(default="http://localhost:8002")

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
