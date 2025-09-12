"""Keyword extraction and subject tagging processors."""

import logging
import re
from collections import Counter
from typing import Any

import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..schemas import KeywordExtractionConfig

logger = logging.getLogger(__name__)

# Subject area keyword mappings following PY LINT HYGIENE
SUBJECT_KEYWORD_MAPPINGS = {
    "mathematics": {
        "algebra",
        "arithmetic",
        "calculus",
        "geometry",
        "statistics",
        "probability",
        "fractions",
        "decimals",
        "equations",
        "variables",
        "functions",
        "graphs",
        "measurement",
        "shapes",
        "angles",
        "perimeter",
        "area",
        "volume",
        "ratio",
        "proportion",
        "percentage",
        "integers",
        "numbers",
        "addition",
        "subtraction",
        "multiplication",
        "division",
        "problem solving",
        "word problems",
        "mathematical thinking",
        "patterns",
        "sequences",
        "data analysis",
        "charts",
        "tables",
        "mean",
        "median",
        "mode",
        "range",
    },
    "language_arts": {
        "reading",
        "writing",
        "vocabulary",
        "grammar",
        "spelling",
        "phonics",
        "comprehension",
        "fluency",
        "literature",
        "poetry",
        "narrative",
        "expository",
        "persuasive",
        "descriptive",
        "characters",
        "plot",
        "setting",
        "theme",
        "main idea",
        "details",
        "inference",
        "context clues",
        "text structure",
        "author purpose",
        "point of view",
        "compare contrast",
        "cause effect",
        "sequence",
        "summary",
        "analysis",
        "essay",
        "paragraph",
        "sentence",
        "punctuation",
        "capitalization",
        "parts of speech",
        "nouns",
        "verbs",
        "adjectives",
        "adverbs",
        "prepositions",
        "conjunctions",
        "pronouns",
        "articles",
        "syllables",
        "phonemes",
        "morphemes",
        "prefixes",
        "suffixes",
        "root words",
    },
    "science": {
        "biology",
        "chemistry",
        "physics",
        "earth science",
        "environmental science",
        "anatomy",
        "physiology",
        "genetics",
        "evolution",
        "ecology",
        "botany",
        "zoology",
        "cells",
        "organisms",
        "ecosystems",
        "photosynthesis",
        "respiration",
        "reproduction",
        "adaptation",
        "classification",
        "scientific method",
        "hypothesis",
        "experiment",
        "observation",
        "data",
        "conclusion",
        "variables",
        "control",
        "measurement",
        "matter",
        "energy",
        "atoms",
        "molecules",
        "elements",
        "compounds",
        "reactions",
        "forces",
        "motion",
        "electricity",
        "magnetism",
        "waves",
        "light",
        "sound",
        "heat",
        "temperature",
        "weather",
        "climate",
        "rocks",
        "minerals",
        "soil",
        "water cycle",
        "solar system",
        "planets",
        "stars",
        "galaxies",
    },
    "social_studies": {
        "history",
        "geography",
        "civics",
        "government",
        "economics",
        "culture",
        "society",
        "community",
        "citizenship",
        "democracy",
        "constitution",
        "rights",
        "responsibilities",
        "laws",
        "elections",
        "voting",
        "leadership",
        "maps",
        "location",
        "place",
        "region",
        "movement",
        "human environment interaction",
        "continents",
        "countries",
        "states",
        "cities",
        "population",
        "migration",
        "trade",
        "transportation",
        "communication",
        "technology",
        "ancient civilizations",
        "world cultures",
        "traditions",
        "holidays",
        "religions",
        "languages",
        "diversity",
        "tolerance",
        "cooperation",
        "conflict resolution",
        "peace",
        "war",
        "revolution",
        "independence",
        "exploration",
        "colonization",
        "immigration",
        "industrial revolution",
        "civil rights",
        "timeline",
        "chronology",
        "cause and effect",
        "change over time",
        "primary sources",
        "secondary sources",
        "artifacts",
        "documents",
    },
    "motor_skills": {
        "gross motor",
        "fine motor",
        "coordination",
        "balance",
        "strength",
        "endurance",
        "flexibility",
        "agility",
        "running",
        "jumping",
        "hopping",
        "skipping",
        "climbing",
        "throwing",
        "catching",
        "kicking",
        "hitting",
        "walking",
        "marching",
        "dancing",
        "swimming",
        "riding",
        "writing",
        "drawing",
        "cutting",
        "pasting",
        "coloring",
        "painting",
        "building",
        "stacking",
        "sorting",
        "manipulating",
        "grasping",
        "pinching",
        "holding",
        "releasing",
        "pointing",
        "reaching",
        "stretching",
        "bending",
        "twisting",
        "turning",
        "body awareness",
        "spatial awareness",
        "directional concepts",
        "left right",
        "up down",
        "in out",
        "over under",
        "front back",
        "near far",
        "safety",
        "rules",
        "equipment",
        "sports",
        "games",
        "recreation",
        "fitness",
        "health",
        "nutrition",
        "hygiene",
    },
    "communication": {
        "speech",
        "language",
        "articulation",
        "pronunciation",
        "fluency",
        "voice",
        "volume",
        "pitch",
        "tone",
        "rate",
        "clarity",
        "expression",
        "listening",
        "understanding",
        "following directions",
        "asking questions",
        "answering questions",
        "conversation",
        "turn taking",
        "eye contact",
        "body language",
        "gestures",
        "facial expressions",
        "nonverbal communication",
        "social skills",
        "pragmatics",
        "greetings",
        "introductions",
        "requests",
        "comments",
        "complaints",
        "apologies",
        "compliments",
        "storytelling",
        "describing",
        "explaining",
        "comparing",
        "sequencing",
        "categorizing",
        "problem solving",
        "reasoning",
        "opinions",
        "feelings",
        "emotions",
        "thoughts",
        "ideas",
        "creativity",
        "imagination",
        "humor",
        "sarcasm",
        "metaphors",
        "idioms",
        "slang",
        "formal informal",
        "appropriate inappropriate",
        "respectful disrespectful",
        "kind mean",
        "helpful unhelpful",
        "cooperative uncooperative",
        "patient impatient",
        "confident shy",
        "outgoing reserved",
        "friendly unfriendly",
        "polite rude",
        "honest dishonest",
        "trustworthy untrustworthy",
    },
    "behavior": {
        "attention",
        "focus",
        "concentration",
        "listening",
        "following directions",
        "completing tasks",
        "staying on task",
        "organization",
        "planning",
        "time management",
        "responsibility",
        "independence",
        "self control",
        "impulse control",
        "emotional regulation",
        "coping strategies",
        "stress management",
        "anger management",
        "conflict resolution",
        "problem solving",
        "decision making",
        "goal setting",
        "motivation",
        "persistence",
        "resilience",
        "flexibility",
        "adaptability",
        "cooperation",
        "collaboration",
        "teamwork",
        "leadership",
        "respect",
        "kindness",
        "empathy",
        "compassion",
        "tolerance",
        "acceptance",
        "inclusion",
        "diversity",
        "fairness",
        "justice",
        "honesty",
        "integrity",
        "trustworthiness",
        "reliability",
        "punctuality",
        "attendance",
        "participation",
        "engagement",
        "enthusiasm",
        "curiosity",
        "initiative",
        "creativity",
        "risk taking",
        "mistakes",
        "learning from failure",
        "growth mindset",
        "self advocacy",
        "self awareness",
        "self confidence",
        "self esteem",
        "self worth",
        "positive attitude",
        "optimism",
        "hope",
        "joy",
        "happiness",
        "pride",
        "satisfaction",
        "accomplishment",
        "success",
        "achievement",
        "progress",
        "improvement",
        "mastery",
        "excellence",
    },
    "adaptive_life_skills": {
        "daily living",
        "self care",
        "personal hygiene",
        "grooming",
        "dressing",
        "eating",
        "drinking",
        "toileting",
        "bathing",
        "brushing teeth",
        "washing hands",
        "combing hair",
        "tying shoes",
        "buttoning",
        "zipping",
        "snapping",
        "velcro",
        "cooking",
        "preparing food",
        "kitchen safety",
        "nutrition",
        "healthy eating",
        "meal planning",
        "grocery shopping",
        "cleaning",
        "organizing",
        "laundry",
        "household chores",
        "time management",
        "scheduling",
        "calendar",
        "money management",
        "budgeting",
        "counting money",
        "making change",
        "banking",
        "shopping",
        "transportation",
        "walking",
        "biking",
        "public transportation",
        "driving",
        "safety",
        "community safety",
        "stranger danger",
        "emergency procedures",
        "first aid",
        "phone skills",
        "communication",
        "social skills",
        "relationships",
        "friendship",
        "family",
        "community",
        "work skills",
        "job skills",
        "employment",
        "volunteering",
        "leisure",
        "recreation",
        "hobbies",
        "interests",
        "entertainment",
        "technology",
        "computer skills",
        "internet safety",
        "digital citizenship",
        "independence",
        "self determination",
        "choice making",
        "problem solving",
        "critical thinking",
        "advocacy",
        "rights",
        "responsibilities",
        "citizenship",
    },
}


class KeywordExtractor:
    """Extract keywords and subject tags from text."""

    def __init__(self) -> None:
        """Initialize keyword extractor."""
        self._ensure_nltk_data()
        self._load_spacy_model()
        self._setup_tfidf()

    def _ensure_nltk_data(self) -> None:
        """Ensure required NLTK data is available."""
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer")
            nltk.download("punkt", quiet=True)

        try:
            nltk.data.find("corpora/stopwords")
        except LookupError:
            logger.info("Downloading NLTK stopwords")
            nltk.download("stopwords", quiet=True)

        try:
            nltk.data.find("taggers/averaged_perceptron_tagger")
        except LookupError:
            logger.info("Downloading NLTK POS tagger")
            nltk.download("averaged_perceptron_tagger", quiet=True)

    def _load_spacy_model(self) -> None:
        """Load spaCy model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy model 'en_core_web_sm' not found. "
                "Install with: python -m spacy download en_core_web_sm",
            )
            self.nlp = None

    def _setup_tfidf(self) -> None:
        """Setup TF-IDF vectorizer."""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words="english",
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.95,
        )

    async def extract_keywords(
        self,
        text: str,
        config: KeywordExtractionConfig | None = None,
    ) -> tuple[list[str], list[str], dict[str, Any]]:
        """Extract keywords and subject tags from text.

        Args:
            text: Input text to process
            config: Extraction configuration

        Returns:
            Tuple of (keywords, subject_tags, metadata)
        """
        if config is None:
            config = KeywordExtractionConfig()

        if not text or not text.strip():
            return [], [], {"extraction_method": "empty_text"}

        # Preprocess text
        cleaned_text = self._preprocess_text(text)

        # Extract keywords using multiple methods
        keywords_methods = {}

        if config.use_tfidf:
            keywords_methods["tfidf"] = await self._extract_tfidf_keywords(
                cleaned_text,
                config,
            )

        if config.use_yake:
            keywords_methods["yake"] = await self._extract_yake_keywords(
                cleaned_text,
                config,
            )

        if config.use_spacy and self.nlp:
            keywords_methods["spacy"] = await self._extract_spacy_keywords(
                cleaned_text,
                config,
            )

        # Combine and rank keywords
        combined_keywords = self._combine_keywords(
            keywords_methods,
            config.max_keywords,
        )

        # Extract subject tags
        subject_tags = self._extract_subject_tags(
            combined_keywords,
            text,
            config.subject_confidence_threshold,
        )

        metadata = {
            "extraction_methods": list(keywords_methods.keys()),
            "total_text_length": len(text),
            "cleaned_text_length": len(cleaned_text),
            "keyword_counts": {
                method: len(keywords) for method, keywords in keywords_methods.items()
            },
            "subject_confidence_threshold": config.subject_confidence_threshold,
        }

        logger.info(
            "Extracted %d keywords and %d subject tags from %d chars of text",
            len(combined_keywords),
            len(subject_tags),
            len(text),
        )

        return combined_keywords, subject_tags, metadata

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for keyword extraction."""
        # Remove extra whitespace and normalize
        text = re.sub(r"\s+", " ", text.strip())

        # Remove special characters but keep word boundaries
        text = re.sub(r"[^\w\s\-']", " ", text)

        # Remove very short words (less than 3 characters)
        words = text.split()
        words = [word for word in words if len(word) >= 3]

        return " ".join(words)

    async def _extract_tfidf_keywords(
        self,
        text: str,
        config: KeywordExtractionConfig,
    ) -> list[str]:
        """Extract keywords using TF-IDF."""
        try:
            # Fit TF-IDF on the text
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([text])

            # Get feature names and scores
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]

            # Create keyword-score pairs
            keyword_scores = list(zip(feature_names, tfidf_scores, strict=False))

            # Sort by score and filter
            keyword_scores.sort(key=lambda x: x[1], reverse=True)

            keywords = [
                keyword
                for keyword, score in keyword_scores
                if score > 0 and len(keyword) >= config.min_keyword_length
            ]

            return keywords[: config.max_keywords * 2]  # Get more for combining

        except Exception as e:
            logger.error("TF-IDF keyword extraction failed: %s", e)
            return []

    async def _extract_yake_keywords(
        self,
        text: str,
        config: KeywordExtractionConfig,
    ) -> list[str]:
        """Extract keywords using YAKE algorithm."""
        try:
            import yake

            kw_extractor = yake.KeywordExtractor(
                lan="en",
                n=3,  # n-gram size
                dedupLim=0.7,
                top=config.max_keywords * 2,
            )

            keywords_scores = kw_extractor.extract_keywords(text)

            # YAKE returns (keyword, score) tuples with lower scores being better
            keywords = [
                keyword
                for keyword, score in keywords_scores
                if len(keyword) >= config.min_keyword_length
            ]

            return keywords

        except ImportError:
            logger.warning("YAKE not available, skipping YAKE extraction")
            return []
        except Exception as e:
            logger.error("YAKE keyword extraction failed: %s", e)
            return []

    async def _extract_spacy_keywords(
        self,
        text: str,
        config: KeywordExtractionConfig,
    ) -> list[str]:
        """Extract keywords using spaCy NLP."""
        if not self.nlp:
            return []

        try:
            doc = self.nlp(text)

            # Extract noun phrases and named entities
            keywords = set()

            # Add noun phrases
            for chunk in doc.noun_chunks:
                phrase = chunk.text.strip().lower()
                if len(phrase) >= config.min_keyword_length:
                    keywords.add(phrase)

            # Add named entities
            for ent in doc.ents:
                entity = ent.text.strip().lower()
                if len(entity) >= config.min_keyword_length:
                    keywords.add(entity)

            # Add important single words (nouns, adjectives)
            for token in doc:
                if (
                    token.pos_ in ["NOUN", "ADJ", "PROPN"]
                    and not token.is_stop
                    and not token.is_punct
                    and len(token.text) >= config.min_keyword_length
                ):
                    keywords.add(token.text.lower())

            return list(keywords)[: config.max_keywords * 2]

        except Exception as e:
            logger.error("spaCy keyword extraction failed: %s", e)
            return []

    def _combine_keywords(
        self,
        keywords_methods: dict[str, list[str]],
        max_keywords: int,
    ) -> list[str]:
        """Combine keywords from different methods."""
        # Count frequency across methods
        keyword_counts = Counter()

        for method_keywords in keywords_methods.values():
            for keyword in method_keywords:
                keyword_counts[keyword] += 1

        # Sort by frequency and then alphabetically
        sorted_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: (-x[1], x[0]),
        )

        # Return top keywords
        return [keyword for keyword, count in sorted_keywords[:max_keywords]]

    def _extract_subject_tags(
        self,
        keywords: list[str],
        original_text: str,
        confidence_threshold: float,
    ) -> list[str]:
        """Extract subject area tags based on keywords."""
        subject_scores = {}

        # Convert text to lowercase for matching
        text_lower = original_text.lower()
        keywords_lower = [kw.lower() for kw in keywords]

        for subject, subject_keywords in SUBJECT_KEYWORD_MAPPINGS.items():
            score = 0.0
            matches = 0

            # Check keyword matches
            for keyword in keywords_lower:
                for subject_keyword in subject_keywords:
                    if (
                        keyword == subject_keyword
                        or keyword in subject_keyword
                        or subject_keyword in keyword
                    ):
                        score += 1.0
                        matches += 1
                        break

            # Check direct text matches
            for subject_keyword in subject_keywords:
                if subject_keyword in text_lower:
                    score += 0.5
                    matches += 1

            # Normalize score
            if matches > 0:
                total_possible = len(subject_keywords)
                normalized_score = min(score / total_possible, 1.0)
                subject_scores[subject] = normalized_score

        # Filter by confidence threshold
        confident_subjects = [
            subject
            for subject, score in subject_scores.items()
            if score >= confidence_threshold
        ]

        # Sort by score
        confident_subjects.sort(
            key=lambda s: subject_scores[s],
            reverse=True,
        )

        return confident_subjects

    async def update_subject_mappings(
        self,
        new_mappings: dict[str, set[str]],
    ) -> None:
        """Update subject keyword mappings.

        Args:
            new_mappings: New mappings to add or update
        """
        global SUBJECT_KEYWORD_MAPPINGS

        for subject, keywords in new_mappings.items():
            if subject in SUBJECT_KEYWORD_MAPPINGS:
                SUBJECT_KEYWORD_MAPPINGS[subject].update(keywords)
            else:
                SUBJECT_KEYWORD_MAPPINGS[subject] = keywords

        logger.info("Updated subject mappings for %d subjects", len(new_mappings))

    async def get_subject_similarities(
        self,
        text: str,
        subjects: list[str] | None = None,
    ) -> dict[str, float]:
        """Get similarity scores for subjects using text analysis.

        Args:
            text: Input text
            subjects: List of subjects to check (default: all)

        Returns:
            Dictionary mapping subjects to similarity scores
        """
        if subjects is None:
            subjects = list(SUBJECT_KEYWORD_MAPPINGS.keys())

        if not text.strip():
            return {subject: 0.0 for subject in subjects}

        try:
            # Create documents for each subject
            subject_docs = []
            subject_names = []

            for subject in subjects:
                if subject in SUBJECT_KEYWORD_MAPPINGS:
                    subject_text = " ".join(SUBJECT_KEYWORD_MAPPINGS[subject])
                    subject_docs.append(subject_text)
                    subject_names.append(subject)

            if not subject_docs:
                return {subject: 0.0 for subject in subjects}

            # Add input text
            all_docs = subject_docs + [text]

            # Calculate TF-IDF similarities
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_docs)

            # Calculate cosine similarities
            input_vector = tfidf_matrix[-1]  # Last document is input text
            subject_vectors = tfidf_matrix[:-1]  # All except last

            similarities = cosine_similarity(input_vector, subject_vectors)[0]

            # Create result dictionary
            result = {}
            for i, subject in enumerate(subject_names):
                result[subject] = float(similarities[i])

            # Add zeros for subjects not in mappings
            for subject in subjects:
                if subject not in result:
                    result[subject] = 0.0

            return result

        except Exception as e:
            logger.error("Subject similarity calculation failed: %s", e)
            return {subject: 0.0 for subject in subjects}
