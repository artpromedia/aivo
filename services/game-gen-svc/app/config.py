"""Game Generation Service configuration."""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Service configuration
    service_name: str = "game-gen-svc"
    service_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # CORS
    cors_origins: list[str] = ["*"]

    # Cache configuration
    cache_enabled: bool = True
    cache_redis_url: str = "redis://localhost:6379/0"
    cache_default_ttl_seconds: int = 3600  # 1 hour
    cache_max_manifest_size_kb: int = 1024  # 1MB

    # Performance targets
    target_generation_time_ms: int = 1000  # ≤1s latency
    max_concurrent_generations: int = 50

    # Template configuration
    templates_directory: str = "/app/templates"
    assets_base_url: str = "https://cdn.example.com/game-assets"

    # Game generation limits
    max_scenes_per_game: int = 10
    max_assets_per_scene: int = 20
    max_game_duration_minutes: int = 60
    min_game_duration_minutes: int = 1

    # Accessibility defaults
    default_audio_cues: bool = True
    default_reduced_motion: bool = False
    default_high_contrast: bool = False

    # AI/ML configuration
    content_generation_model: str = "gpt-4"
    content_generation_api_key: str = ""
    difficulty_assessment_enabled: bool = True

    # Monitoring
    metrics_enabled: bool = True
    health_check_timeout_seconds: int = 5

    # Database (for template storage)
    database_url: str = "postgresql://localhost/game_gen"

    # Subject-specific settings
    math_game_types: list[str] = ["number_line", "puzzle", "sorting", "quiz"]
    english_game_types: list[str] = [
        "word_builder", "matching", "quiz", "drag_drop"
    ]
    science_game_types: list[str] = ["quiz", "matching", "sorting", "puzzle"]
    art_game_types: list[str] = ["drawing", "matching", "memory", "puzzle"]
    music_game_types: list[str] = ["rhythm", "memory", "matching", "quiz"]

    model_config = ConfigDict(env_prefix="GAME_GEN_", case_sensitive=False)


# Global settings instance
settings = Settings()
