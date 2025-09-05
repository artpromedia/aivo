"""Configuration settings for Analytics Service."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service settings
    service_name: str = Field(
        default="analytics-svc", description="Service name"
    )
    debug: bool = Field(default=False, description="Debug mode")

    # Snowflake settings
    snowflake_account: str = Field(
        default="", description="Snowflake account identifier"
    )
    snowflake_user: str = Field(default="", description="Snowflake username")
    snowflake_password: str = Field(
        default="", description="Snowflake password"
    )
    snowflake_warehouse: str = Field(
        default="COMPUTE_WH", description="Snowflake warehouse"
    )
    snowflake_database: str = Field(
        default="AIVO_ANALYTICS", description="Snowflake database"
    )
    snowflake_schema: str = Field(
        default="PUBLIC", description="Snowflake schema"
    )
    snowflake_role: str = Field(
        default="ACCOUNTADMIN", description="Snowflake role"
    )

    # Differential Privacy settings
    dp_epsilon: float = Field(
        default=1.0, description="Differential privacy epsilon parameter"
    )
    dp_sensitivity: float = Field(
        default=1.0, description="Differential privacy sensitivity parameter"
    )

    # Cache settings
    cache_ttl_seconds: int = Field(
        default=30, description="Cache TTL in seconds"
    )

    # OpenTelemetry settings
    otel_endpoint: str = Field(
        default="http://jaeger:14250", description="OTEL collector endpoint"
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False
