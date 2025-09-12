"""Configuration for the Subject-Brain service."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service Configuration
    service_name: str = "subject-brain-svc"
    service_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["*"]

    # Database Configuration
    database_url: str = Field(
        default="postgresql://user:pass@localhost:5432/subject_brain",
        description="PostgreSQL database URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis cache URL")

    # Kubernetes Configuration
    k8s_namespace: str = "subject-brain"
    k8s_service_account: str = "subject-brain-sa"
    k8s_config_path: str | None = None  # None for in-cluster config

    # GPU Configuration
    gpu_node_selector: dict[str, str] = Field(
        default_factory=lambda: {"accelerator": "nvidia-tesla-v100"}
    )
    gpu_resource_requests: dict[str, str] = Field(default_factory=lambda: {"nvidia.com/gpu": "1"})
    gpu_resource_limits: dict[str, str] = Field(default_factory=lambda: {"nvidia.com/gpu": "1"})

    # Autoscaling Configuration
    hpa_enabled: bool = True
    hpa_min_replicas: int = 0
    hpa_max_replicas: int = 100
    hpa_target_gpu_queue_depth: int = 10
    hpa_target_cpu_utilization: int = 70
    hpa_target_memory_utilization: int = 80
    hpa_scale_down_delay_seconds: int = 300
    hpa_scale_up_delay_seconds: int = 30

    # Runtime Configuration
    default_ttl_seconds: int = 300  # 5 minutes
    max_runtime_minutes: int = 120  # 2 hours
    default_memory_mb: int = 2048
    default_cpu_cores: float = 1.0
    max_concurrent_runtimes: int = 50

    # Planner Configuration
    planner_model_path: str = "/models/subject-brain-v1"
    planner_cache_ttl_seconds: int = 3600  # 1 hour
    max_activities_per_plan: int = 10
    default_session_duration_minutes: int = 30

    # Monitoring Configuration
    metrics_enabled: bool = True
    metrics_port: int = 9090
    health_check_interval_seconds: int = 30
    metrics_collection_interval_seconds: int = 15

    # External Services
    auth_service_url: str = "http://auth-svc:8000"
    learner_service_url: str = "http://learner-svc:8000"
    coursework_service_url: str = "http://coursework-svc:8000"
    analytics_service_url: str = "http://analytics-svc:8000"

    # Security
    api_key_header: str = "X-API-Key"
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for token validation",
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_prefix = "SUBJECT_BRAIN_"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
