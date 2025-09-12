"""
Content moderation service with Perspective API integration.
"""

import asyncio
import hashlib
import logging
import re
import time
from typing import Dict

import httpx
from pydantic import BaseModel

from ..models import ModerationAction
from ..schemas import ModerationResult, PIIDetectionResult

logger = logging.getLogger(__name__)


class PerspectiveConfig(BaseModel):
    """Perspective API configuration."""

    api_key: str
    endpoint: str = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
    timeout: int = 10
    retry_attempts: int = 3
    rate_limit_per_second: int = 10


class PIIDetector:
    """PII detection and scrubbing."""

    # PII patterns
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PHONE_PATTERN = re.compile(
        r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"
    )
    SSN_PATTERN = re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b")
    CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    ADDRESS_PATTERN = re.compile(
        r"\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b",
        re.IGNORECASE,
    )

    @classmethod
    def detect_pii(cls, text: str) -> PIIDetectionResult:
        """Detect PII in text."""
        pii_types = []
        confidence = 0.0
        scrubbed_content = text

        if cls.EMAIL_PATTERN.search(text):
            pii_types.append("email")
            scrubbed_content = cls.EMAIL_PATTERN.sub("[EMAIL_REDACTED]", scrubbed_content)
            confidence = max(confidence, 0.95)

        if cls.PHONE_PATTERN.search(text):
            pii_types.append("phone")
            scrubbed_content = cls.PHONE_PATTERN.sub("[PHONE_REDACTED]", scrubbed_content)
            confidence = max(confidence, 0.90)

        if cls.SSN_PATTERN.search(text):
            pii_types.append("ssn")
            scrubbed_content = cls.SSN_PATTERN.sub("[SSN_REDACTED]", scrubbed_content)
            confidence = max(confidence, 0.98)

        if cls.CREDIT_CARD_PATTERN.search(text):
            pii_types.append("credit_card")
            scrubbed_content = cls.CREDIT_CARD_PATTERN.sub("[CARD_REDACTED]", scrubbed_content)
            confidence = max(confidence, 0.95)

        if cls.ADDRESS_PATTERN.search(text):
            pii_types.append("address")
            scrubbed_content = cls.ADDRESS_PATTERN.sub("[ADDRESS_REDACTED]", scrubbed_content)
            confidence = max(confidence, 0.85)

        contains_pii = len(pii_types) > 0

        return PIIDetectionResult(
            contains_pii=contains_pii,
            pii_types=pii_types,
            confidence=confidence,
            scrubbed_content=scrubbed_content if contains_pii else None,
        )


class PerspectiveAPI:
    """Google Perspective API client."""

    def __init__(self, config: PerspectiveConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)
        self._rate_limiter = asyncio.Semaphore(config.rate_limit_per_second)

    async def analyze_comment(self, text: str) -> Dict[str, float]:
        """Analyze comment using Perspective API."""
        async with self._rate_limiter:
            request_data = {
                "comment": {"text": text},
                "requestedAttributes": {
                    "TOXICITY": {},
                    "SEVERE_TOXICITY": {},
                    "IDENTITY_ATTACK": {},
                    "INSULT": {},
                    "PROFANITY": {},
                    "THREAT": {},
                },
                "languages": ["en"],
                "doNotStore": True,
            }

            for attempt in range(self.config.retry_attempts):
                try:
                    response = await self.client.post(
                        self.config.endpoint, params={"key": self.config.api_key}, json=request_data
                    )
                    response.raise_for_status()

                    data = response.json()
                    scores = {}

                    for attribute, result in data.get("attributeScores", {}).items():
                        scores[attribute.lower()] = result["summaryScore"]["value"]

                    return scores

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limited
                        await asyncio.sleep(2**attempt)
                        continue
                    logger.error(f"Perspective API HTTP error: {e}")
                    raise
                except Exception as e:
                    logger.error(f"Perspective API error (attempt {attempt + 1}): {e}")
                    if attempt == self.config.retry_attempts - 1:
                        raise
                    await asyncio.sleep(1)

        return {}

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class ModerationService:
    """Content moderation service."""

    def __init__(self, perspective_config: PerspectiveConfig):
        self.perspective = PerspectiveAPI(perspective_config)
        self.pii_detector = PIIDetector()

        # Thresholds for moderation decisions
        self.thresholds = {"soft_block": 0.7, "hard_block": 0.85, "human_review": 0.8}

    async def moderate_message(
        self, content: str, moderation_level: str = "strict"
    ) -> ModerationResult:
        """Moderate a message and return action to take."""
        start_time = time.time()

        try:
            # Adjust thresholds based on moderation level
            thresholds = self._get_thresholds_for_level(moderation_level)

            # Check for PII first
            pii_result = self.pii_detector.detect_pii(content)
            if pii_result.contains_pii:
                processing_time = int((time.time() - start_time) * 1000)
                return ModerationResult(
                    action=ModerationAction.PII_SCRUBBED,
                    confidence=pii_result.confidence,
                    reason=f"PII detected: {', '.join(pii_result.pii_types)}",
                    processing_time_ms=processing_time,
                )

            # Analyze with Perspective API
            scores = await self.perspective.analyze_comment(content)

            # Calculate overall toxicity score
            toxicity_score = scores.get("toxicity", 0.0)
            threat_score = scores.get("threat", 0.0)
            profanity_score = scores.get("profanity", 0.0)
            identity_attack_score = scores.get("identity_attack", 0.0)

            # Determine action based on scores
            max_score = max(toxicity_score, threat_score, identity_attack_score)

            if max_score >= thresholds["hard_block"]:
                action = ModerationAction.HARD_BLOCK
                reason = f"High toxicity detected (score: {max_score:.2f})"
            elif max_score >= thresholds["soft_block"]:
                if max_score >= thresholds["human_review"]:
                    action = ModerationAction.HUMAN_REVIEW
                    reason = f"Content flagged for human review (score: {max_score:.2f})"
                else:
                    action = ModerationAction.SOFT_BLOCK
                    reason = f"Moderate toxicity detected (score: {max_score:.2f})"
            else:
                action = ModerationAction.APPROVED
                reason = "Content approved"

            processing_time = int((time.time() - start_time) * 1000)

            return ModerationResult(
                action=action,
                confidence=max_score,
                reason=reason,
                toxicity_score=toxicity_score,
                threat_score=threat_score,
                profanity_score=profanity_score,
                identity_attack_score=identity_attack_score,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Moderation error: {e}")
            processing_time = int((time.time() - start_time) * 1000)

            # Fail safe - flag for human review on errors
            return ModerationResult(
                action=ModerationAction.HUMAN_REVIEW,
                confidence=0.0,
                reason=f"Moderation service error: {str(e)}",
                processing_time_ms=processing_time,
            )

    def _get_thresholds_for_level(self, level: str) -> Dict[str, float]:
        """Get moderation thresholds based on level."""
        if level == "strict":
            return {"soft_block": 0.5, "hard_block": 0.75, "human_review": 0.7}
        elif level == "moderate":
            return {"soft_block": 0.7, "hard_block": 0.85, "human_review": 0.8}
        elif level == "relaxed":
            return {"soft_block": 0.8, "hard_block": 0.9, "human_review": 0.85}
        else:
            return self.thresholds

    async def close(self):
        """Close moderation service."""
        await self.perspective.close()


def create_content_hash(content: str) -> str:
    """Create SHA-256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
