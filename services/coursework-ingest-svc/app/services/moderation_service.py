"""Content moderation service using OpenAI and custom filters."""

import logging
import re
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class ModerationService:
    """Service for content moderation and safety checks."""

    def __init__(self) -> None:
        """Initialize content moderation service."""
        self.openai_client = None
        if settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Define inappropriate content patterns
        self.inappropriate_patterns = [
            r"\b(?:hate|violence|harassment|bullying)\b",
            r"\b(?:discrimination|racism|sexism)\b",
            r"\b(?:explicit|pornographic|sexual)\b",
            r"\b(?:suicide|self-harm|depression)\b",
            r"\b(?:drug|alcohol|substance)\s+(?:abuse|use)\b",
        ]

        # Compile patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.inappropriate_patterns
        ]

    async def moderate_content(self, text: str) -> dict[str, Any]:
        """Moderate content using multiple methods."""
        try:
            # Start with rule-based filtering
            rule_based_result = await self._rule_based_moderation(text)

            # Use OpenAI moderation if available
            openai_result = None
            if self.openai_client:
                openai_result = await self._openai_moderation(text)

            # Combine results
            combined_score = self._combine_moderation_scores(
                rule_based_result, openai_result
            )

            # Determine approval based on threshold
            approved = combined_score >= settings.moderation_threshold

            return {
                "score": combined_score,
                "approved": approved,
                "flags": {
                    "rule_based": rule_based_result,
                    "openai": openai_result,
                },
                "threshold": settings.moderation_threshold,
            }

        except (ValueError, AttributeError, TypeError) as e:
            logger.error("Error in content moderation: %s", e)
            # Default to requiring manual review on error
            return {
                "score": 0.5,
                "approved": False,
                "error": str(e),
                "flags": {"error": True},
            }

    async def _rule_based_moderation(self, text: str) -> dict[str, Any]:
        """Apply rule-based content moderation."""
        if not text or not text.strip():
            return {"score": 1.0, "flags": [], "method": "rule_based"}

        text_lower = text.lower()
        flags = []

        # Check for inappropriate patterns
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(text)
            if matches:
                flags.append({
                    "pattern_id": i,
                    "pattern": self.inappropriate_patterns[i],
                    "matches": matches,
                })

        # Check for excessive profanity (simple word list)
        profanity_words = [
            "damn", "shit", "fuck", "bitch", "ass", "hell",
            "crap", "piss", "bastard", "slut", "whore"
        ]
        profanity_count = sum(
            text_lower.count(word) for word in profanity_words
        )
        total_words = len(text.split())
        profanity_ratio = profanity_count / max(total_words, 1)

        if profanity_ratio > 0.1:  # More than 10% profanity
            flags.append({
                "type": "excessive_profanity",
                "ratio": profanity_ratio,
                "count": profanity_count,
            })

        # Calculate score based on flags
        if not flags:
            score = 1.0  # Clean content
        elif len(flags) == 1 and profanity_ratio < 0.05:
            score = 0.8  # Minor issues
        elif len(flags) <= 2:
            score = 0.6  # Moderate issues
        else:
            score = 0.3  # Major issues

        return {
            "score": score,
            "flags": flags,
            "method": "rule_based",
            "profanity_ratio": profanity_ratio,
        }

    async def _openai_moderation(self, text: str) -> dict[str, Any] | None:
        """Use OpenAI's moderation API."""
        if not self.openai_client:
            return None

        try:
            response = await self.openai_client.moderations.create(input=text)
            result = response.results[0]

            # Convert OpenAI result to our format
            flagged_categories = [
                category
                for category, flagged in result.categories.model_dump().items()
                if flagged
            ]

            # Calculate overall score from category scores
            category_scores = result.category_scores.model_dump()
            if category_scores:
                max_score = max(category_scores.values())
            else:
                max_score = 0.0

            # Invert score (OpenAI gives violation probability, we want safety)
            safety_score = 1.0 - max_score

            return {
                "score": safety_score,
                "flagged": result.flagged,
                "categories": flagged_categories,
                "category_scores": category_scores,
                "method": "openai",
            }

        except (ValueError, AttributeError, TypeError) as e:
            logger.error("OpenAI moderation error: %s", e)
            return None

    def _combine_moderation_scores(
        self,
        rule_based: dict[str, Any],
        openai_result: dict[str, Any] | None,
    ) -> float:
        """Combine scores from different moderation methods."""
        rule_score = rule_based.get("score", 0.5)

        if not openai_result:
            return rule_score

        openai_score = openai_result.get("score", 0.5)

        # Take the more conservative (lower) score
        # Weight OpenAI slightly higher as it's more sophisticated
        combined_score = (0.4 * rule_score) + (0.6 * openai_score)

        # If either method flags content as highly problematic, be conservative
        if rule_score < 0.5 or openai_score < 0.5:
            combined_score = min(combined_score, 0.6)

        return combined_score
