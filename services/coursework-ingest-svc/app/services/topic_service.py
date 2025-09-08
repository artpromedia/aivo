"""Topic extraction service using OpenAI and transformers."""

import json
import logging
import re
from collections import Counter
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class TopicExtractionService:
    """Service for extracting topics from text content."""

    def __init__(self) -> None:
        """Initialize topic extraction service."""
        self.openai_client = None
        if settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def extract_topics(self, text: str) -> dict[str, Any]:
        """Extract topics from text using available methods."""
        try:
            if not text or not text.strip():
                return {
                    "topics": [],
                    "confidence": 1.0,
                    "method": "empty_text",
                }

            # Use OpenAI for topic extraction if available
            if self.openai_client:
                return await self._openai_topic_extraction(text)
            else:
                return await self._fallback_topic_extraction(text)

        except (ValueError, AttributeError, TypeError) as e:
            logger.error("Error in topic extraction: %s", e)
            return {
                "topics": [],
                "confidence": 0.0,
                "error": str(e),
            }

    async def _openai_topic_extraction(self, text: str) -> dict[str, Any]:
        """Use OpenAI for sophisticated topic extraction."""
        try:
            prompt = f"""
            Analyze this educational content and extract main topics.

            Respond with JSON containing:
            - "topics": Main topics/subjects (max 10)
            - "key_concepts": Important concepts (max 15)
            - "academic_level": Level (elementary/middle/high_school/college)
            - "subject_areas": Academic subjects (math/science/english/history)
            - "difficulty": Difficulty level (1-10)
            - "summary": Brief 2-3 sentence summary

            Content: {text[:2000]}
            """

            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert educational content analyzer. "
                            "Provide structured analysis in valid JSON format."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            # Try to parse JSON response
            try:
                topics_data = json.loads(content)
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse OpenAI JSON response, using fallback"
                )
                return await self._fallback_topic_extraction(text)

            # Validate and structure the response
            structured_topics = {
                "topics": topics_data.get("topics", [])[:10],
                "key_concepts": topics_data.get("key_concepts", [])[:15],
                "academic_level": topics_data.get("academic_level", "unknown"),
                "subject_areas": topics_data.get("subject_areas", []),
                "difficulty": min(
                    max(topics_data.get("difficulty", 5), 1), 10
                ),
                "summary": topics_data.get("summary", ""),
                "confidence": 0.9,
                "method": "openai",
            }

            return structured_topics

        except (
            ValueError,
            AttributeError,
            TypeError,
            json.JSONDecodeError,
        ) as e:
            logger.error("OpenAI topic extraction error: %s", e)
            return await self._fallback_topic_extraction(text)

    async def _fallback_topic_extraction(self, text: str) -> dict[str, Any]:
        """Fallback topic extraction using keyword analysis."""
        # Define subject-specific keywords
        subject_keywords = {
            "mathematics": [
                "equation",
                "algebra",
                "geometry",
                "calculus",
                "trigonometry",
                "statistics",
                "probability",
                "function",
                "derivative",
                "integral",
                "matrix",
                "vector",
                "polynomial",
                "theorem",
            ],
            "science": [
                "experiment",
                "hypothesis",
                "theory",
                "molecule",
                "atom",
                "chemical",
                "biology",
                "physics",
                "chemistry",
                "DNA",
                "cell",
                "evolution",
                "energy",
                "force",
                "gravity",
            ],
            "english": [
                "literature",
                "grammar",
                "vocabulary",
                "essay",
                "paragraph",
                "metaphor",
                "simile",
                "character",
                "plot",
                "theme",
                "analysis",
                "poetry",
                "prose",
                "narrative",
            ],
            "history": [
                "historical",
                "century",
                "war",
                "revolution",
                "government",
                "political",
                "democracy",
                "constitution",
                "empire",
                "civilization",
                "culture",
                "society",
                "timeline",
            ],
            "geography": [
                "continent",
                "country",
                "climate",
                "population",
                "mountain",
                "ocean",
                "river",
                "city",
                "capital",
                "border",
                "latitude",
                "longitude",
                "map",
                "region",
            ],
        }

        # Convert text to lowercase for analysis
        text_lower = text.lower()

        # Count subject-related keywords
        subject_scores = {}
        for subject, keywords in subject_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                subject_scores[subject] = score

        # Extract general topics using noun phrases
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text)
        word_counts = Counter(word.lower() for word in words)

        # Filter common words
        stop_words = {
            "the",
            "and",
            "that",
            "have",
            "for",
            "not",
            "with",
            "you",
            "this",
            "but",
            "his",
            "from",
            "they",
            "she",
            "her",
            "been",
            "than",
            "its",
            "who",
            "oil",
            "sit",
            "now",
            "into",
            "can",
        }

        significant_words = [
            word
            for word, count in word_counts.most_common(20)
            if count >= 2 and word not in stop_words and len(word) > 3
        ]

        # Estimate academic level based on word complexity
        complex_words = [word for word in words if len(word) > 8]
        complexity_ratio = len(complex_words) / max(len(words), 1)

        if complexity_ratio < 0.05:
            academic_level = "elementary"
        elif complexity_ratio < 0.1:
            academic_level = "middle_school"
        elif complexity_ratio < 0.15:
            academic_level = "high_school"
        else:
            academic_level = "college"

        # Estimate difficulty based on text characteristics
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
        difficulty = min(max(int(avg_word_length - 2), 1), 10)

        # Create summary
        top_subjects = list(subject_scores.keys())[:3]
        summary = (
            f"Educational content with {len(words)} words "
            f"focusing on {', '.join(top_subjects)}"
        )

        return {
            "topics": significant_words[:10],
            "key_concepts": significant_words[:15],
            "academic_level": academic_level,
            "subject_areas": list(subject_scores.keys()),
            "difficulty": difficulty,
            "summary": summary,
            "confidence": 0.6,
            "method": "fallback_keyword",
            "word_count": len(words),
            "complexity_ratio": complexity_ratio,
        }
