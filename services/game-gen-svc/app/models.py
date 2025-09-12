"""Game Generation Service models."""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    version: str
    timestamp: float


class PerformanceStats(BaseModel):
    """Service performance statistics."""

    total_generations: int
    average_generation_time_ms: float
    target_time_ms: int
    cache_hit_rate: float
    cache_size_bytes: int
    service_uptime_seconds: float


class SubjectType(str, Enum):
    """Subject types supported by the game generation system."""

    MATH = "math"
    ENGLISH = "english"
    SCIENCE = "science"
    SOCIAL_STUDIES = "social_studies"
    ART = "art"
    MUSIC = "music"
    PHYSICAL_EDUCATION = "physical_education"


class GameType(str, Enum):
    """Types of mini-games that can be generated."""

    PUZZLE = "puzzle"
    QUIZ = "quiz"
    MATCHING = "matching"
    SORTING = "sorting"
    DRAWING = "drawing"
    RHYTHM = "rhythm"
    MEMORY = "memory"
    WORD_BUILDER = "word_builder"
    NUMBER_LINE = "number_line"
    DRAG_DROP = "drag_drop"


class DifficultyLevel(str, Enum):
    """Game difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AccessibilitySettings(BaseModel):
    """Accessibility configuration for games."""

    reduced_motion: bool = Field(
        default=False, description="Reduce or eliminate animations and motion effects"
    )
    high_contrast: bool = Field(
        default=False, description="Use high contrast colors for better visibility"
    )
    large_text: bool = Field(default=False, description="Use larger text sizes")
    audio_cues: bool = Field(default=True, description="Enable audio feedback and cues")
    simplified_ui: bool = Field(default=False, description="Use simplified user interface elements")
    color_blind_friendly: bool = Field(
        default=False, description="Use color-blind friendly color palette"
    )


class GameAsset(BaseModel):
    """Game asset definition."""

    asset_id: str = Field(description="Unique asset identifier")
    asset_type: str = Field(description="Type of asset (image, audio, video, model)")
    url: str = Field(description="URL to the asset")
    alt_text: str | None = Field(default=None, description="Alternative text for accessibility")
    size_bytes: int | None = Field(default=None, description="Asset size in bytes")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional asset metadata")


class GameScene(BaseModel):
    """Game scene definition."""

    scene_id: str = Field(description="Unique scene identifier")
    name: str = Field(description="Scene display name")
    description: str = Field(description="Scene description")
    duration_seconds: int = Field(description="Expected scene duration")
    assets: list[GameAsset] = Field(default_factory=list, description="Assets used in this scene")
    interactions: list[dict[str, Any]] = Field(
        default_factory=list, description="Interactive elements and their configurations"
    )
    learning_objectives: list[str] = Field(
        default_factory=list, description="What the learner should achieve in this scene"
    )
    accessibility_adaptations: dict[str, Any] = Field(
        default_factory=dict, description="Scene-specific accessibility modifications"
    )


class ScoringConfig(BaseModel):
    """Game scoring configuration."""

    max_points: int = Field(description="Maximum points possible")
    time_bonus: bool = Field(default=True, description="Whether to award time-based bonuses")
    accuracy_weight: float = Field(default=0.7, description="Weight of accuracy in final score")
    speed_weight: float = Field(default=0.3, description="Weight of speed in final score")
    hint_penalty: int = Field(default=5, description="Points deducted per hint used")
    completion_bonus: int = Field(default=50, description="Bonus points for completing the game")


class GameManifest(BaseModel):
    """Complete game manifest with scenes, assets, and configuration."""

    manifest_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique manifest identifier"
    )
    learner_id: str = Field(description="Target learner identifier")
    subject: SubjectType = Field(description="Subject area")
    grade: int = Field(description="Grade level (K-12)")
    game_type: GameType = Field(description="Type of mini-game")
    difficulty: DifficultyLevel = Field(description="Game difficulty level")
    duration_minutes: int = Field(description="Estimated playtime in minutes")

    # Game content
    title: str = Field(description="Game title")
    description: str = Field(description="Game description")
    scenes: list[GameScene] = Field(description="Game scenes in order")
    scoring: ScoringConfig = Field(description="Scoring configuration")

    # Accessibility
    accessibility: AccessibilitySettings = Field(
        default_factory=AccessibilitySettings, description="Accessibility configuration"
    )

    # Metadata
    created_at: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp(),
        description="Manifest creation timestamp (Unix timestamp)",
    )
    template_id: str | None = Field(default=None, description="Base template used for generation")
    cache_key: str | None = Field(default=None, description="Cache key for fast retrieval")
    tags: list[str] = Field(default_factory=list, description="Game tags for categorization")


class ManifestRequest(BaseModel):
    """Request to generate a game manifest."""

    learner_id: str = Field(description="Target learner identifier")
    subject: SubjectType = Field(description="Subject area")
    duration_minutes: int = Field(ge=1, le=60, description="Desired game duration in minutes")
    grade: int | None = Field(
        default=None, ge=0, le=12, description="Grade level (K-12), auto-detected if not provided"
    )
    difficulty: DifficultyLevel | None = Field(
        default=None, description="Preferred difficulty, auto-selected if not provided"
    )
    game_type: GameType | None = Field(
        default=None, description="Preferred game type, auto-selected if not provided"
    )
    accessibility: AccessibilitySettings | None = Field(
        default=None, description="Accessibility preferences"
    )
    preferred_topics: list[str] = Field(
        default_factory=list, description="Specific topics to focus on"
    )


class ManifestResponse(BaseModel):
    """Response containing the generated game manifest."""

    manifest: GameManifest = Field(description="Generated game manifest")
    generation_time_ms: int = Field(description="Time taken to generate manifest")
    cache_hit: bool = Field(description="Whether result came from cache")
    recommendations: list[str] = Field(
        default_factory=list, description="Additional game recommendations"
    )


class TemplateInfo(BaseModel):
    """Information about a game template."""

    template_id: str = Field(description="Template identifier")
    name: str = Field(description="Template name")
    description: str = Field(description="Template description")
    subject: SubjectType = Field(description="Subject area")
    game_type: GameType = Field(description="Game type")
    supported_grades: list[int] = Field(description="Supported grade levels")
    estimated_generation_time_ms: int = Field(description="Typical generation time")
    accessibility_features: list[str] = Field(description="Supported accessibility features")


class CacheStats(BaseModel):
    """Cache performance statistics."""

    hit_count: int = Field(description="Number of cache hits")
    miss_count: int = Field(description="Number of cache misses")
    hit_rate: float = Field(description="Cache hit rate percentage")
    size_bytes: int = Field(description="Cache size in bytes")
    num_entries: int = Field(description="Number of cache entries")
    redis_connected: bool = Field(description="Redis connection status")
