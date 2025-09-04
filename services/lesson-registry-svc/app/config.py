"""Configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App settings
    app_name: str = "Lesson Registry Service"
    version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = ("postgresql+asyncpg://postgres:postgres@localhost"
                         ":5432/lesson_registry")

    # AWS/MinIO settings
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    s3_bucket: str = "lesson-assets"
    s3_endpoint_url: str | None = None  # For MinIO
    cloudfront_domain: str | None = None
    asset_url_expiry: int = 600  # 10 minutes

    # Auth settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # RBAC
    admin_roles: list[str] = ["admin", "district_admin"]
    teacher_roles: list[str] = ["teacher", "instructor"]

    # Search settings
    search_page_size: int = 20
    max_search_results: int = 1000

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


settings = Settings()
