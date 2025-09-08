"""Search service configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service config
    service_name: str = Field(default="search-svc", description="Service name")
    environment: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Log level")

    # API config
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8003, description="Port to listen on")
    api_prefix: str = Field(default="/api/v1", description="API prefix")

    # OpenSearch config
    opensearch_host: str = Field(
        default="localhost",
        description="OpenSearch host"
    )
    opensearch_port: int = Field(
        default=9200,
        description="OpenSearch port"
    )
    opensearch_use_ssl: bool = Field(
        default=False,
        description="Use SSL for OpenSearch"
    )
    opensearch_verify_certs: bool = Field(
        default=False,
        description="Verify SSL certificates"
    )
    opensearch_username: str = Field(
        default="",
        description="OpenSearch username"
    )
    opensearch_password: str = Field(
        default="",
        description="OpenSearch password"
    )

    # Index settings
    lessons_index: str = Field(
        default="lessons",
        description="Lessons index name"
    )
    coursework_index: str = Field(
        default="coursework",
        description="Coursework index name"
    )
    learners_index: str = Field(
        default="learners",
        description="Learners index name"
    )

    # Redis config (for caching)
    redis_host: str = Field(
        default="localhost",
        description="Redis host"
    )
    redis_port: int = Field(
        default=6379,
        description="Redis port"
    )
    redis_db: int = Field(
        default=0,
        description="Redis database"
    )
    redis_password: str = Field(
        default="",
        description="Redis password"
    )

    # RBAC settings
    enable_rbac: bool = Field(
        default=True,
        description="Enable RBAC filtering"
    )
    jwt_secret_key: str = Field(
        default="your-secret-key",
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )

    # PII masking settings
    enable_pii_masking: bool = Field(
        default=True, description="Enable PII masking"
    )
    mask_names: bool = Field(default=True, description="Mask learner names")
    mask_emails: bool = Field(default=True, description="Mask email addresses")
    mask_ids: bool = Field(default=True, description="Mask sensitive IDs")

    # Search settings
    default_search_size: int = Field(
        default=20, description="Default search result size"
    )
    max_search_size: int = Field(
        default=100, description="Maximum search result size"
    )
    search_timeout_seconds: int = Field(
        default=30, description="Search timeout in seconds"
    )
    suggestion_size: int = Field(
        default=5, description="Number of suggestions to return"
    )

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_prefix = "SEARCH_"


settings = Settings()
