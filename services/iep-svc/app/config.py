"""
Configuration settings for IEP Service.
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server configuration
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # GraphQL configuration
    graphql_path: str = Field(default="/graphql", description="GraphQL endpoint path")
    graphiql_enabled: bool = Field(default=True, description="Enable GraphiQL interface")
    
    # CRDT configuration
    crdt_sync_interval: int = Field(default=30, description="CRDT sync interval in seconds")
    crdt_conflict_resolution: str = Field(default="last_write_wins", description="CRDT conflict resolution strategy")
    
    # Approval service configuration
    approval_service_url: str = Field(
        default="http://localhost:8080/approvals",
        description="Approval service base URL"
    )
    approval_timeout: float = Field(default=30.0, description="Approval service timeout")
    dual_approval_required: bool = Field(default=True, description="Require dual approval")
    
    # Event publishing configuration
    event_endpoint: str = Field(
        default="http://localhost:8080/events",
        description="Event publishing endpoint"
    )
    event_timeout: float = Field(default=10.0, description="Event publishing timeout")
    
    # IEP document settings
    max_goals_per_iep: int = Field(default=10, description="Maximum goals per IEP")
    max_accommodations_per_iep: int = Field(default=20, description="Maximum accommodations per IEP")
    iep_expiry_days: int = Field(default=365, description="IEP expiry in days")
    
    # Security settings
    jwt_secret_key: str = Field(default="your-secret-key", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_hours: int = Field(default=24, description="JWT expiration hours")
    
    class Config:
        env_file = ".env"
        env_prefix = "IEP_"


# Global settings instance
settings = Settings()
