"""PII detection and masking service using Presidio."""

import logging
import re
from typing import Any

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except ImportError:
    # Fallback if presidio is not available
    AnalyzerEngine = None
    AnonymizerEngine = None

from app.config import settings

logger = logging.getLogger(__name__)


class PIIService:
    """Service for PII detection and masking."""

    def __init__(self) -> None:
        """Initialize PII service."""
        self.analyzer = None
        self.anonymizer = None

        if AnalyzerEngine and AnonymizerEngine:
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                logger.info("Presidio PII detection initialized successfully")
            except (ImportError, AttributeError, ValueError) as e:
                logger.warning("Failed to initialize Presidio: %s", e)
        else:
            logger.warning(
                "Presidio not available, using fallback PII detection"
            )

    async def detect_and_mask_pii(self, text: str) -> dict[str, Any]:
        """Detect and mask PII in text."""
        try:
            if self.analyzer and self.anonymizer:
                return await self._presidio_detection(text)
            else:
                return await self._fallback_detection(text)

        except (ValueError, AttributeError, TypeError) as e:
            logger.error("Error in PII detection: %s", e)
            return {
                "pii_detected": False,
                "entities": [],
                "masked_text": text,
                "confidence": 0.0,
                "error": str(e),
            }

    async def _presidio_detection(self, text: str) -> dict[str, Any]:
        """Use Presidio for PII detection and masking."""
        if not text or not text.strip():
            return {
                "pii_detected": False,
                "entities": [],
                "masked_text": text,
                "confidence": 1.0,
            }

        # Analyze text for PII
        analyzer_results = self.analyzer.analyze(
            text=text,
            entities=settings.pii_entities,
            language="en",
        )

        # Filter by confidence threshold
        high_confidence_results = [
            result
            for result in analyzer_results
            if result.score >= 0.7  # High confidence threshold
        ]

        pii_detected = len(high_confidence_results) > 0

        # Anonymize text if PII found
        masked_text = text
        if pii_detected:
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=high_confidence_results,
            )
            masked_text = anonymized_result.text

        # Convert results to serializable format
        entities = []
        for result in high_confidence_results:
            entities.append(
                {
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start : result.end],
                }
            )

        # Calculate overall confidence
        if entities:
            total_score = sum(entity["score"] for entity in entities)
            avg_confidence = total_score / len(entities)
        else:
            avg_confidence = 1.0  # High confidence in no PII

        return {
            "pii_detected": pii_detected,
            "entities": entities,
            "masked_text": masked_text,
            "confidence": avg_confidence,
            "method": "presidio",
        }

    async def _fallback_detection(self, text: str) -> dict[str, Any]:
        """Fallback PII detection using regex patterns."""
        if not text or not text.strip():
            return {
                "pii_detected": False,
                "entities": [],
                "masked_text": text,
                "confidence": 1.0,
            }

        # Define basic PII patterns
        patterns = {
            "EMAIL_ADDRESS": (
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            ),
            "PHONE_NUMBER": (
                r"\b\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b"
            ),
            "SSN": r"\b\d{3}-?\d{2}-?\d{4}\b",
            "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        }

        entities = []
        masked_text = text

        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(
                    {
                        "entity_type": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "score": 0.8,  # Default confidence for regex matches
                        "text": match.group(),
                    }
                )

                # Mask the detected PII
                mask_char = "*"
                mask_length = len(match.group())
                if entity_type == "EMAIL_ADDRESS":
                    # Keep domain visible for emails
                    email_parts = match.group().split("@")
                    if len(email_parts) == 2:
                        masked_local = mask_char * len(email_parts[0])
                        replacement = f"{masked_local}@{email_parts[1]}"
                    else:
                        replacement = mask_char * mask_length
                else:
                    replacement = mask_char * mask_length

                masked_text = (
                    masked_text[: match.start()]
                    + replacement
                    + masked_text[match.end() :]
                )

        pii_detected = len(entities) > 0

        return {
            "pii_detected": pii_detected,
            "entities": entities,
            "masked_text": masked_text,
            "confidence": 0.8 if entities else 1.0,
            "method": "fallback_regex",
        }
