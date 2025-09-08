"""
PII detection and anonymization services using Presidio.
"""

import logging
import re

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

from .config import settings
from .schemas import PIIEntity

logger = logging.getLogger(__name__)


class PIIService:
    """Service for PII detection and anonymization."""

    def __init__(self) -> None:
        """Initialize PII service with Presidio engines."""
        self.analyzer = None
        self.anonymizer = None
        self._initialize_fallback_patterns()
        self._initialize_engines()

    def _initialize_fallback_patterns(self) -> None:
        """Initialize fallback regex patterns for PII detection."""
        import re

        self.fallback_patterns = {
            "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "PHONE_NUMBER": re.compile(
                r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"
            ),
            "US_SSN": re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
            "CREDIT_CARD": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
            "PERSON": re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),
        }

    def _initialize_engines(self) -> None:
        """Initialize Presidio analyzer and anonymizer engines."""
        try:
            # Configure NLP engine
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
            }

            # Create NLP engine
            nlp_engine_provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = nlp_engine_provider.create_engine()

            # Initialize analyzer
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

            # Initialize anonymizer
            self.anonymizer = AnonymizerEngine()

            logger.info("PII service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize PII service: {e}")
            # Create fallback regex-based service
            self._initialize_fallback()

    def _initialize_fallback(self) -> None:
        """Initialize fallback regex-based PII detection."""
        self.fallback_patterns = {
            "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "PHONE_NUMBER": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            "US_SSN": re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
            "CREDIT_CARD": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        }
        logger.info("Initialized fallback regex-based PII detection")

    async def detect_pii(self, text: str, language: str = "en") -> list[PIIEntity]:
        """
        Detect PII entities in text.

        Args:
            text: Input text to analyze
            language: Language code for analysis

        Returns:
            List of detected PII entities
        """
        if not settings.pii_detection_enabled:
            return []

        entities = []

        try:
            if self.analyzer:
                # Use Presidio analyzer
                results = self.analyzer.analyze(text=text, language=language)

                for result in results:
                    entity = PIIEntity(
                        entity_type=result.entity_type,
                        start=result.start,
                        end=result.end,
                        score=result.score,
                        text=text[result.start : result.end],
                    )
                    entities.append(entity)
            else:
                # Use fallback regex patterns
                entities = self._detect_pii_fallback(text)

        except Exception as e:
            logger.error(f"Error detecting PII: {e}")
            # Fallback to regex patterns
            entities = self._detect_pii_fallback(text)

        logger.info(f"Detected {len(entities)} PII entities in text")
        return entities

    def _detect_pii_fallback(self, text: str) -> list[PIIEntity]:
        """Fallback PII detection using regex patterns."""
        entities = []

        for entity_type, pattern in self.fallback_patterns.items():
            for match in pattern.finditer(text):
                entity = PIIEntity(
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end(),
                    score=0.8,  # Default confidence for regex matches
                    text=match.group(),
                )
                entities.append(entity)

        return entities

    async def anonymize_text(self, text: str, entities: list[PIIEntity]) -> str:
        """
        Anonymize PII entities in text.

        Args:
            text: Original text
            entities: PII entities to anonymize

        Returns:
            Anonymized text
        """
        if not settings.pii_anonymization_enabled or not entities:
            return text

        try:
            if self.anonymizer and self.analyzer:
                # Convert PIIEntity to Presidio format
                analyzer_results = []
                from presidio_analyzer import RecognizerResult

                for entity in entities:
                    result = RecognizerResult(
                        entity_type=entity.entity_type,
                        start=entity.start,
                        end=entity.end,
                        score=entity.score,
                    )
                    analyzer_results.append(result)

                # Anonymize using Presidio
                anonymized_result = self.anonymizer.anonymize(
                    text=text, analyzer_results=analyzer_results
                )
                return anonymized_result.text
            else:
                # Use fallback anonymization
                return self._anonymize_fallback(text, entities)

        except Exception as e:
            logger.error(f"Error anonymizing text: {e}")
            return self._anonymize_fallback(text, entities)

    def _anonymize_fallback(self, text: str, entities: list[PIIEntity]) -> str:
        """Fallback anonymization by replacing with placeholders."""
        # Sort entities by start position (descending) to avoid index issues
        sorted_entities = sorted(entities, key=lambda x: x.start, reverse=True)

        anonymized_text = text
        for entity in sorted_entities:
            placeholder = f"[{entity.entity_type}]"
            anonymized_text = (
                anonymized_text[: entity.start] + placeholder + anonymized_text[entity.end :]
            )

        return anonymized_text

    async def process_text(
        self, text: str, language: str = "en"
    ) -> tuple[str, list[PIIEntity], bool]:
        """
        Process text for PII detection and anonymization.

        Args:
            text: Input text
            language: Language code

        Returns:
            Tuple of (processed_text, detected_entities, was_scrubbed)
        """
        # Detect PII entities
        entities = await self.detect_pii(text, language)

        # Anonymize if entities found
        if entities and settings.pii_anonymization_enabled:
            processed_text = await self.anonymize_text(text, entities)
            return processed_text, entities, True

        return text, entities, False


# Global PII service instance
pii_service = PIIService()
