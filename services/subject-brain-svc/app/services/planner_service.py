"""Subject-Brain Planner Service.

Handles activity planning based on learner baseline, mastery levels,
coursework topics, and teacher constraints.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from ..config import settings
from ..models import (
    ActivityPlan,
    ActivityType,
    CourseworkTopic,
    LearnerBaseline,
    MasteryLevel,
    PlannedActivity,
    PlannerInput,
    TeacherConstraints,
)

logger = logging.getLogger(__name__)


class SubjectBrainPlanner:
    """AI-powered planner for personalized learning activities."""

    def __init__(self) -> None:
        """Initialize the planner."""
        self.model_path = settings.planner_model_path
        self.cache_ttl = settings.planner_cache_ttl_seconds
        self.max_activities = settings.max_activities_per_plan

    async def create_activity_plan(
        self,
        planner_input: PlannerInput
    ) -> ActivityPlan:
        """Create a personalized activity plan for a learner."""
        logger.info(
            "Creating plan for learner %s in %s",
            planner_input.learner_id,
            planner_input.subject,
        )

        # Analyze learner baseline and mastery levels
        analysis = self._analyze_learner_needs(
            planner_input.baseline,
            planner_input.available_topics
        )

        # Filter topics based on teacher constraints
        filtered_topics = self._apply_teacher_constraints(
            planner_input.available_topics, planner_input.teacher_constraints
        )

        # Generate activity sequence
        activities = await self._generate_activity_sequence(
            analysis,
            filtered_topics,
            planner_input.teacher_constraints,
            planner_input.session_duration_minutes,
        )

        # Create the final plan
        plan = ActivityPlan(
            learner_id=planner_input.learner_id,
            subject=planner_input.subject,
            activities=activities,
            total_duration_minutes=sum(
                a.estimated_duration_minutes for a in activities
            ),
            expires_at=datetime.utcnow() + timedelta(
                seconds=self.cache_ttl
            ),
        )

        logger.info(
            "Created plan %s with %d activities", plan.plan_id, len(activities)
        )
        return plan

    def _analyze_learner_needs(
        self,
        baseline: LearnerBaseline,
        available_topics: list[CourseworkTopic],
    ) -> dict[str, Any]:
        """Analyze learner baseline to identify learning needs."""
        analysis = {
            "struggling_topics": [],
            "mastered_topics": [],
            "ready_for_advancement": [],
            "prerequisite_gaps": [],
            "recommended_focus": [],
        }

        # Identify struggling areas (below proficient)
        for topic, mastery in baseline.mastery_levels.items():
            if mastery in [
                MasteryLevel.NOT_STARTED,
                MasteryLevel.BEGINNING
            ]:
                analysis["struggling_topics"].append(topic)
            elif mastery == MasteryLevel.DEVELOPING:
                analysis["recommended_focus"].append(topic)
            elif mastery == MasteryLevel.ADVANCED:
                analysis["mastered_topics"].append(topic)
                analysis["ready_for_advancement"].append(topic)

        # Check for prerequisite gaps
        for topic in available_topics:
            for prereq in topic.prerequisites:
                if prereq not in baseline.mastery_levels:
                    analysis["prerequisite_gaps"].append(
                        {
                            "topic": topic.topic_id,
                            "missing_prerequisite": prereq,
                        }
                    )

        return analysis

    def _apply_teacher_constraints(
        self, topics: list[CourseworkTopic], constraints: TeacherConstraints
    ) -> list[CourseworkTopic]:
        """Filter topics based on teacher constraints."""
        filtered = []

        for topic in topics:
            # Skip blocked topics
            if topic.topic_id in constraints.blocked_topics:
                continue

            # Include required topics
            if topic.topic_id in constraints.required_topics:
                filtered.append(topic)
                continue

            # Apply general filtering logic
            if topic.subject == constraints.subject:
                filtered.append(topic)

        return filtered

    async def _generate_activity_sequence(
        self,
        analysis: dict[str, Any],
        topics: list[CourseworkTopic],
        constraints: TeacherConstraints,
        session_duration: int,
    ) -> list[PlannedActivity]:
        """Generate optimal sequence of learning activities."""
        activities = []
        remaining_time = session_duration

        # Prioritize based on learning needs
        prioritized_topics = self._prioritize_topics(analysis, topics)

        for topic in prioritized_topics:
            if remaining_time <= 0 or len(activities) >= self.max_activities:
                break

            activity = await self._create_activity_for_topic(
                topic, analysis, constraints, remaining_time
            )

            if (
                activity
                and activity.estimated_duration_minutes <= remaining_time
            ):
                activities.append(activity)
                remaining_time -= activity.estimated_duration_minutes

        return activities

    def _prioritize_topics(
        self, analysis: dict[str, Any], topics: list[CourseworkTopic]
    ) -> list[CourseworkTopic]:
        """Prioritize topics based on learner needs analysis."""
        priority_map = {}

        for topic in topics:
            priority = 0

            # High priority for struggling topics
            if topic.topic_id in analysis["struggling_topics"]:
                priority += 10

            # Medium priority for recommended focus
            if topic.topic_id in analysis["recommended_focus"]:
                priority += 5

            # Lower priority for mastered topics (enrichment)
            if topic.topic_id in analysis["mastered_topics"]:
                priority += 2

            # Penalty for prerequisite gaps
            for gap in analysis["prerequisite_gaps"]:
                if gap["topic"] == topic.topic_id:
                    priority -= 3

            priority_map[topic.topic_id] = priority

        # Sort by priority (descending)
        return sorted(
            topics, key=lambda t: priority_map.get(t.topic_id, 0), reverse=True
        )

    async def _create_activity_for_topic(
        self,
        topic: CourseworkTopic,
        analysis: dict[str, Any],
        constraints: TeacherConstraints,
        remaining_time: int,
    ) -> PlannedActivity | None:
        """Create a specific activity for a topic."""
        # Determine activity type based on needs
        activity_type = self._determine_activity_type(
            topic, analysis, constraints
        )

        if not activity_type:
            return None

        # Adjust difficulty based on mastery level
        difficulty_adjustment = 1.0
        if topic.topic_id in analysis["struggling_topics"]:
            difficulty_adjustment = 0.7  # Easier
        elif topic.topic_id in analysis["mastered_topics"]:
            difficulty_adjustment = 1.3  # More challenging

        # Estimate duration (cap at remaining time)
        base_duration = min(
            topic.estimated_duration_minutes,
            remaining_time,
            constraints.max_activity_duration_minutes,
        )

        # Check prerequisites
        prerequisites_met = all(
            prereq in analysis.get("mastered_topics", [])
            for prereq in topic.prerequisites
        )

        rationale = self._generate_rationale(
            topic, activity_type, analysis, difficulty_adjustment
        )

        return PlannedActivity(
            type=activity_type,
            topic=topic,
            estimated_duration_minutes=base_duration,
            difficulty_adjustment=difficulty_adjustment,
            learning_objectives=topic.learning_objectives,
            prerequisites_met=prerequisites_met,
            rationale=rationale,
        )

    def _determine_activity_type(
        self,
        topic: CourseworkTopic,
        analysis: dict[str, Any],
        constraints: TeacherConstraints,
    ) -> ActivityType | None:
        """Determine the best activity type for a topic."""
        # Check teacher preferences first
        if constraints.preferred_activity_types:
            for activity_type in constraints.preferred_activity_types:
                if self._is_activity_appropriate(
                    activity_type, topic, analysis
                ):
                    return activity_type

        # Default logic based on mastery level
        if topic.topic_id in analysis["struggling_topics"]:
            return ActivityType.LESSON  # Need instruction
        elif topic.topic_id in analysis["recommended_focus"]:
            return ActivityType.PRACTICE  # Need practice
        elif topic.topic_id in analysis["mastered_topics"]:
            return ActivityType.ENRICHMENT  # Ready for challenge
        else:
            return ActivityType.LESSON  # Default to instruction

    def _is_activity_appropriate(
        self,
        activity_type: ActivityType,
        topic: CourseworkTopic,
        analysis: dict[str, Any],
    ) -> bool:
        """Check if an activity type is appropriate for the topic."""
        # Assessment requires some baseline knowledge
        if activity_type == ActivityType.ASSESSMENT:
            return topic.topic_id not in analysis["struggling_topics"]

        # Enrichment requires mastery
        if activity_type == ActivityType.ENRICHMENT:
            return topic.topic_id in analysis["mastered_topics"]

        # Remediation for struggling topics
        if activity_type == ActivityType.REMEDIATION:
            return topic.topic_id in analysis["struggling_topics"]

        # Lessons and practice are generally appropriate
        return True

    def _generate_rationale(
        self,
        topic: CourseworkTopic,
        activity_type: ActivityType,
        analysis: dict[str, Any],
        difficulty_adjustment: float,
    ) -> str:
        """Generate human-readable rationale for activity selection."""
        rationale_parts = []

        # Base reason
        if topic.topic_id in analysis["struggling_topics"]:
            rationale_parts.append(
                f"Learner needs foundational support in {topic.name}"
            )
        elif topic.topic_id in analysis["recommended_focus"]:
            rationale_parts.append(
                f"Good opportunity to strengthen {topic.name} skills"
            )
        elif topic.topic_id in analysis["mastered_topics"]:
            rationale_parts.append(
                f"Learner ready for advanced work in {topic.name}"
            )

        # Activity type reason
        activity_reasons = {
            ActivityType.LESSON: "structured instruction",
            ActivityType.PRACTICE: "skill reinforcement",
            ActivityType.ASSESSMENT: "progress evaluation",
            ActivityType.REMEDIATION: "targeted support",
            ActivityType.ENRICHMENT: "advanced exploration",
        }
        rationale_parts.append(
            f"Using {activity_reasons[activity_type]} approach"
        )

        # Difficulty adjustment
        if difficulty_adjustment < 1.0:
            rationale_parts.append("with simplified content")
        elif difficulty_adjustment > 1.0:
            rationale_parts.append("with increased challenge")

        return ". ".join(rationale_parts) + "."


# Global planner instance
planner = SubjectBrainPlanner()
