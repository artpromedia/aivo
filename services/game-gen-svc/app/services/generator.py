"""Game generation service with accessibility and performance optimization."""

import random
import time
from typing import Any

from app.config import settings
from app.models import (
    AccessibilitySettings,
    DifficultyLevel,
    GameAsset,
    GameManifest,
    GameScene,
    GameType,
    ScoringConfig,
    SubjectType,
)


class GameGenerationService:
    """Service for generating accessible game manifests with ≤1s latency."""

    def __init__(self) -> None:
        """Initialize game generation service."""
        self.generation_count = 0
        self.total_generation_time = 0.0

    async def generate_manifest(
        self,
        learner_id: str,
        subject: SubjectType,
        grade: int,
        duration_minutes: int,
        accessibility: AccessibilitySettings,
    ) -> GameManifest:
        """Generate a complete game manifest for learner."""
        start_time = time.time()

        try:
            # Determine appropriate game type for subject
            game_type = self._select_game_type(subject, grade)
            difficulty = self._calculate_difficulty(grade)

            # Generate game scenes based on duration
            num_scenes = self._calculate_scene_count(
                duration_minutes, difficulty
            )
            scenes = []

            for scene_index in range(num_scenes):
                scene = await self._generate_scene(
                    subject,
                    game_type,
                    difficulty,
                    scene_index,
                    accessibility,
                    duration_minutes
                )
                scenes.append(scene)

            # Generate scoring configuration
            scoring = self._generate_scoring_config(
                subject, game_type, difficulty
            )

            # Apply accessibility adaptations
            scenes = self._apply_accessibility_adaptations(
                scenes, accessibility
            )

            # Create manifest
            manifest = GameManifest(
                learner_id=learner_id,
                subject=subject,
                grade=grade,
                game_type=game_type,
                difficulty=difficulty,
                duration_minutes=duration_minutes,
                title=(
                    f"{subject.value.title()} {game_type.value.title()} Game"
                ),
                description=(
                    f"A {difficulty.value} level {subject.value} game "
                    f"for grade {grade}"
                ),
                scenes=scenes,
                scoring=scoring,
                accessibility=accessibility,
            )

            # Update performance metrics
            generation_time = time.time() - start_time
            self.generation_count += 1
            self.total_generation_time += generation_time

            return manifest

        except Exception as e:
            print("Game generation failed: %s", str(e))
            raise

    def _select_game_type(self, subject: SubjectType, grade: int) -> GameType:
        """Select appropriate game type for subject and grade."""
        subject_games = {
            SubjectType.MATH: [
                GameType.PUZZLE, GameType.QUIZ, GameType.SORTING
            ],
            SubjectType.ENGLISH: [
                GameType.WORD_BUILDER, GameType.MATCHING, GameType.QUIZ
            ],
            SubjectType.SCIENCE: [
                GameType.QUIZ, GameType.MATCHING, GameType.SORTING
            ],
            SubjectType.ART: [
                GameType.DRAWING, GameType.MATCHING, GameType.MEMORY
            ],
            SubjectType.MUSIC: [
                GameType.RHYTHM, GameType.MEMORY, GameType.MATCHING
            ],
        }

        available_games = subject_games.get(subject, [GameType.QUIZ])

        # Adjust for grade level
        if grade <= 2:
            # Simpler games for younger students
            simple_games = [
                GameType.MATCHING, GameType.SORTING, GameType.MEMORY
            ]
            available_games = [
                g for g in available_games if g in simple_games
            ] or simple_games

        return random.choice(available_games)

    def _calculate_difficulty(self, grade: int) -> DifficultyLevel:
        """Calculate difficulty based on grade level."""
        if grade <= 2:
            return DifficultyLevel.BEGINNER
        elif grade <= 5:
            return DifficultyLevel.INTERMEDIATE
        elif grade <= 8:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.EXPERT

    def _calculate_scene_count(
        self, duration_minutes: int, difficulty: DifficultyLevel
    ) -> int:
        """Calculate number of scenes based on duration and difficulty."""
        base_scenes = max(1, duration_minutes // 3)  # ~3 minutes per scene

        # Adjust for difficulty
        if difficulty == DifficultyLevel.BEGINNER:
            return min(base_scenes, 3)
        elif difficulty == DifficultyLevel.INTERMEDIATE:
            return min(base_scenes, 5)
        elif difficulty == DifficultyLevel.ADVANCED:
            return min(base_scenes, 8)
        else:
            return min(base_scenes, settings.max_scenes_per_game)

    async def _generate_scene(
        self,
        subject: SubjectType,
        game_type: GameType,
        difficulty: DifficultyLevel,
        scene_index: int,
        accessibility: AccessibilitySettings,
        duration_minutes: int,
    ) -> GameScene:
        """Generate a single game scene."""
        scene_id = f"scene_{scene_index + 1}"

        # Generate scene content based on subject and game type
        title, instructions = self._generate_scene_content(
            subject, game_type, difficulty, scene_index
        )

        # Generate assets for the scene
        assets = self._generate_scene_assets(
            subject, game_type, difficulty, accessibility
        )

        # Calculate scene duration
        scene_count = self._calculate_scene_count(duration_minutes, difficulty)
        scene_duration = max(30, duration_minutes * 60 // scene_count)

        return GameScene(
            scene_id=scene_id,
            name=title,
            description=instructions,
            duration_seconds=scene_duration,
            assets=assets,
            interactions=[],  # Will be populated by frontend
            learning_objectives=[],  # Could be enhanced later
            accessibility_adaptations={},
        )

    def _generate_scene_content(
        self,
        subject: SubjectType,
        game_type: GameType,
        difficulty: DifficultyLevel,  # pylint: disable=unused-argument
        scene_index: int,  # pylint: disable=unused-argument
    ) -> tuple[str, str]:
        """Generate scene title and instructions."""
        content_templates = {
            (SubjectType.MATH, GameType.PUZZLE): (
                f"Math Puzzle {scene_index + 1}",
                "Solve the puzzle by arranging the numbers correctly.",
            ),
            (SubjectType.MATH, GameType.QUIZ): (
                f"Math Challenge {scene_index + 1}",
                "Answer the math questions as quickly and accurately "
                "as possible.",
            ),
            (SubjectType.ENGLISH, GameType.WORD_BUILDER): (
                f"Word Builder {scene_index + 1}",
                "Build words by connecting the letter tiles.",
            ),
            (SubjectType.ENGLISH, GameType.MATCHING): (
                f"Word Matching {scene_index + 1}",
                "Match words with their correct definitions or images.",
            ),
            (SubjectType.SCIENCE, GameType.QUIZ): (
                f"Science Explorer {scene_index + 1}",
                "Test your knowledge of science concepts.",
            ),
            (SubjectType.ART, GameType.DRAWING): (
                f"Art Creation {scene_index + 1}",
                "Use the tools to create your artwork following the theme.",
            ),
            (SubjectType.MUSIC, GameType.RHYTHM): (
                f"Rhythm Master {scene_index + 1}",
                "Follow the rhythm pattern and tap at the right time.",
            ),
        }

        return content_templates.get(
            (subject, game_type),
            (
                f"Challenge {scene_index + 1}",
                "Complete the challenge to proceed."
            ),
        )

    def _generate_scene_assets(
        self,
        subject: SubjectType,
        game_type: GameType,
        difficulty: DifficultyLevel,  # pylint: disable=unused-argument
        accessibility: AccessibilitySettings,
    ) -> list[GameAsset]:
        """Generate assets for a scene."""
        assets = []

        # Background asset
        bg_asset = GameAsset(
            asset_id="background",
            asset_type="image",
            url=(
                f"{settings.assets_base_url}/backgrounds/"
                f"{subject.value}_bg.jpg"
            ),
            alt_text=f"{subject.value} themed background",
            width=1920,
            height=1080,
        )
        assets.append(bg_asset)

        # Game-specific assets
        if game_type == GameType.PUZZLE:
            for i in range(6):
                piece_asset = GameAsset(
                    asset_id=f"puzzle_piece_{i}",
                    asset_type="image",
                    url=(
                        f"{settings.assets_base_url}/puzzle/"
                        f"{subject.value}_piece_{i}.png"
                    ),
                    alt_text=f"Puzzle piece {i + 1}",
                    width=100,
                    height=100,
                )
                assets.append(piece_asset)

        elif game_type == GameType.QUIZ:
            # Question audio for accessibility
            if accessibility.audio_cues:
                audio_asset = GameAsset(
                    asset_id="question_audio",
                    asset_type="audio",
                    url=(
                        f"{settings.assets_base_url}/audio/"
                        f"{subject.value}_question.mp3"
                    ),
                    alt_text="Question audio narration",
                )
                assets.append(audio_asset)

        elif game_type == GameType.MATCHING:
            for i in range(4):
                card_asset = GameAsset(
                    asset_id=f"match_card_{i}",
                    asset_type="image",
                    url=(
                        f"{settings.assets_base_url}/cards/"
                        f"{subject.value}_card_{i}.png"
                    ),
                    alt_text=f"Matching card {i + 1}",
                    width=150,
                    height=200,
                )
                assets.append(card_asset)

        # Add accessibility-specific assets
        if accessibility.high_contrast:
            # High contrast overlay
            contrast_asset = GameAsset(
                asset_id="high_contrast_overlay",
                asset_type="css",
                url=f"{settings.assets_base_url}/styles/high_contrast.css",
                alt_text="High contrast styling",
            )
            assets.append(contrast_asset)

        return assets[: settings.max_assets_per_scene]

    def _calculate_required_interactions(
        self, game_type: GameType, difficulty: DifficultyLevel
    ) -> int:
        """Calculate required interactions for scene completion."""
        base_interactions = {
            GameType.PUZZLE: 6,
            GameType.QUIZ: 3,
            GameType.MATCHING: 4,
            GameType.SORTING: 5,
            GameType.WORD_BUILDER: 4,
            GameType.DRAWING: 1,
            GameType.MEMORY: 8,
            GameType.RHYTHM: 10,
            GameType.DRAG_DROP: 6,
        }

        base_count = base_interactions.get(game_type, 3)

        # Adjust for difficulty
        multipliers = {
            DifficultyLevel.BEGINNER: 0.7,
            DifficultyLevel.INTERMEDIATE: 1.0,
            DifficultyLevel.ADVANCED: 1.3,
            DifficultyLevel.EXPERT: 1.6,
        }

        return max(1, int(base_count * multipliers[difficulty]))

    def _generate_scoring_config(
        self,
        subject: SubjectType,  # pylint: disable=unused-argument
        game_type: GameType,  # pylint: disable=unused-argument
        difficulty: DifficultyLevel,
    ) -> ScoringConfig:
        """Generate scoring configuration for the game."""
        base_points = {
            DifficultyLevel.BEGINNER: 10,
            DifficultyLevel.INTERMEDIATE: 20,
            DifficultyLevel.ADVANCED: 30,
            DifficultyLevel.EXPERT: 50,
        }

        return ScoringConfig(
            max_points=base_points[difficulty] * 10,  # Max points
            time_bonus=difficulty in [
                DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT
            ],
            accuracy_weight=0.7,
            speed_weight=0.3,
            hint_penalty=5 if difficulty != DifficultyLevel.BEGINNER else 0,
            completion_bonus=base_points[difficulty] * 2,
        )

    def _apply_accessibility_adaptations(
        self, scenes: list[GameScene], accessibility: AccessibilitySettings
    ) -> list[GameScene]:
        """Apply accessibility adaptations to game scenes."""
        adapted_scenes = []

        for scene in scenes:
            adapted_scene = scene.model_copy()

            # Modify description for accessibility
            if accessibility.simplified_ui:
                description = scene.description
                adapted_scene.description = self._simplify_instructions(
                    description
                )

            # Adjust timing for reduced motion
            if accessibility.reduced_motion:
                adapted_scene.duration_seconds = int(
                    scene.duration_seconds * 1.5
                )

            adapted_scenes.append(adapted_scene)

        return adapted_scenes

    def _simplify_instructions(self, instructions: str) -> str:
        """Simplify instructions for better accessibility."""
        # Split into shorter sentences
        sentences = instructions.split(". ")
        if len(sentences) > 1:
            return sentences[0] + "."
        return instructions

    def get_performance_stats(self) -> dict[str, Any]:
        """Get service performance statistics."""
        avg_generation_time = 0.0
        if self.generation_count > 0:
            generation_time = self.total_generation_time
            avg_generation_time = generation_time / self.generation_count

        return {
            "total_generations": self.generation_count,
            "average_generation_time_ms": avg_generation_time * 1000,
            "target_time_ms": settings.target_generation_time_ms,
            "performance_ratio": (
                (avg_generation_time * 1000)
                / settings.target_generation_time_ms
                if avg_generation_time > 0
                else 0
            ),
        }


# Global service instance
game_generation_service = GameGenerationService()
