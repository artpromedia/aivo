"""
Core service implementations for speech processing and journaling.
"""

import re
from datetime import datetime, timedelta

try:
    # pylint: disable=import-error
    # pyright: ignore[reportMissingImports]
    import librosa
except ImportError:
    librosa = None  # Optional dependency for audio processing

import numpy as np
from cryptography.fernet import Fernet

from .config import Settings
from .schemas import (
    ArticulationScore,
    PhonemeTimingData,
    PrivacyLevel,
    SentimentAnalysis,
    SentimentType,
)

settings = Settings()


class SpeechProcessor:
    """Speech processing and articulation analysis."""

    def __init__(self):
        self.sample_rate = settings.sample_rate

    def extract_phoneme_timing(
        self,
        audio_path: str,
        target_phonemes: list[str]
    ) -> list[PhonemeTimingData]:
        """
        Extract phoneme timing from audio file.

        Args:
            audio_path: Path to audio file
            target_phonemes: Expected phonemes to detect

        Returns:
            List of phoneme timing data
        """
        if librosa is None:
            print("Warning: librosa not available. Audio processing disabled.")
            return []

        try:
            # Load audio file
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)

            # Extract MFCC features for phoneme detection
            # (unused in this simplified implementation)
            _ = librosa.feature.mfcc(
                y=audio,
                sr=sr,
                n_mfcc=13
            )

            # Simple onset detection for timing
            onset_frames = librosa.onset.onset_detect(
                y=audio,
                sr=sr,
                units="time"
            )

            # Advanced phoneme detection using onset detection and spectral
            # analysis
            phoneme_data = []
            num_segments = min(len(target_phonemes), len(onset_frames) - 1)

            for i in range(num_segments):
                phoneme = target_phonemes[i]
                start_time = onset_frames[i]
                end_time = (
                    onset_frames[i + 1] if i + 1 < len(onset_frames)
                    else len(audio) / sr
                )

                # Extract audio segment for analysis
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                segment = audio[start_sample:end_sample]

                # Advanced confidence calculation using multiple features
                confidence = self._calculate_advanced_confidence(
                    segment, phoneme, sr
                )

                # Detect actual phoneme using spectral features
                detected_phoneme = self._detect_phoneme(segment, sr)

                phoneme_data.append(PhonemeTimingData(
                    phoneme=detected_phoneme or phoneme,
                    start_time=start_time,
                    end_time=end_time,
                    confidence=confidence,
                    expected_phoneme=phoneme
                ))

            return phoneme_data

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error processing audio: {e}")
            return []

    def _calculate_confidence(self, audio_segment: np.ndarray) -> float:
        """Calculate confidence score for audio segment."""
        if len(audio_segment) == 0:
            return 0.0

        # Simple confidence based on RMS energy and zero-crossing rate
        rms_energy = np.sqrt(np.mean(audio_segment**2))
        zcr = np.mean(librosa.feature.zero_crossing_rate(audio_segment))

        # Normalize and combine metrics
        confidence = min(rms_energy * 2 + (1 - zcr), 1.0)
        return max(confidence, 0.0)

    def _calculate_advanced_confidence(
        self, segment: np.ndarray, phoneme: str, sr: int
    ) -> float:
        """Calculate advanced confidence using multiple acoustic features."""
        if len(segment) == 0 or librosa is None:
            return 0.0

        try:
            # Extract multiple features
            rms_energy = np.sqrt(np.mean(segment**2))
            zcr = np.mean(librosa.feature.zero_crossing_rate(segment))
            spectral_centroid = np.mean(
                librosa.feature.spectral_centroid(y=segment, sr=sr)
            )
            mfcc = librosa.feature.mfcc(y=segment, sr=sr, n_mfcc=13)
            mfcc_mean = np.mean(mfcc)

            # Phoneme-specific feature weighting
            vowel_phonemes = ["a", "e", "i", "o", "u", "æ", "ɛ", "ɪ", "ɔ", "ʊ"]
            is_vowel = phoneme.lower() in vowel_phonemes

            if is_vowel:
                # Vowels: emphasize spectral stability and formant clarity
                confidence = (
                    rms_energy * 0.4 + (1 - zcr) * 0.3 +
                    (spectral_centroid / 4000) * 0.2 + abs(mfcc_mean) * 0.1
                )
            else:
                # Consonants: emphasize onset clarity and spectral dynamics
                confidence = (
                    rms_energy * 0.3 + zcr * 0.3 +
                    (spectral_centroid / 4000) * 0.3 + abs(mfcc_mean) * 0.1
                )

            return min(max(confidence, 0.0), 1.0)

        except Exception:  # pylint: disable=broad-exception-caught
            return self._calculate_confidence(segment)

    def _detect_phoneme(self, segment: np.ndarray, sr: int) -> str | None:
        """Detect phoneme using spectral analysis."""
        if len(segment) == 0 or librosa is None:
            return None

        try:
            # Extract MFCC features for phoneme classification
            mfcc = librosa.feature.mfcc(y=segment, sr=sr, n_mfcc=13)
            spectral_centroid = np.mean(
                librosa.feature.spectral_centroid(y=segment, sr=sr)
            )
            zcr = np.mean(librosa.feature.zero_crossing_rate(segment))

            # Simple phoneme classification based on acoustic properties
            # In production, this would use a trained neural network
            if spectral_centroid < 1000 and zcr < 0.1:
                # Low frequency, stable - likely vowel
                if np.mean(mfcc[1]) < -10:
                    return "a"  # Low vowel
                elif np.mean(mfcc[2]) > 10:
                    return "i"  # High vowel
                else:
                    return "e"  # Mid vowel
            elif zcr > 0.3:
                # High zero-crossing rate - fricative
                if spectral_centroid > 3000:
                    return "s"  # High-frequency fricative
                else:
                    return "f"  # Lower-frequency fricative
            elif spectral_centroid < 500:
                # Low frequency - nasal or liquid
                return "n"
            else:
                # Likely plosive
                return "p"

        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def score_articulation(
        self,
        phoneme_data: list[PhonemeTimingData]
    ) -> list[ArticulationScore]:
        """
        Score articulation quality based on phoneme timing.

        Args:
            phoneme_data: Phoneme timing data

        Returns:
            Articulation scores
        """
        scores = []

        for phoneme in phoneme_data:
            # Base accuracy on confidence
            accuracy = phoneme.confidence

            # Timing score based on phoneme duration
            duration = phoneme.end_time - phoneme.start_time
            optimal_duration = self._get_optimal_duration(
                phoneme.phoneme
            )
            timing_score = (
                1.0 - abs(duration - optimal_duration) / optimal_duration
            )
            timing_score = max(0.0, min(1.0, timing_score))

            # Consistency score (would be calculated across multiple attempts)
            consistency_score = accuracy  # Simplified

            # Fluency score based on timing smoothness
            fluency_score = (accuracy + timing_score) / 2

            # Overall weighted score
            overall_score = (
                accuracy * settings.scoring_weights["accuracy"] +
                timing_score * settings.scoring_weights["timing"] +
                consistency_score * settings.scoring_weights["consistency"] +
                fluency_score * settings.scoring_weights["fluency"]
            )

            # Generate feedback
            feedback = self._generate_feedback(
                phoneme.phoneme, accuracy, timing_score
            )

            scores.append(ArticulationScore(
                phoneme=phoneme.phoneme,
                accuracy_score=accuracy,
                timing_score=timing_score,
                consistency_score=consistency_score,
                fluency_score=fluency_score,
                overall_score=overall_score,
                feedback=feedback
            ))

        return scores

    def _get_optimal_duration(self, phoneme: str) -> float:
        """Get optimal duration for phoneme in seconds."""
        # Simplified phoneme duration mapping
        vowel_duration = 0.15
        consonant_duration = 0.10

        vowels = {"a", "e", "i", "o", "u", "æ", "ɛ", "ɪ", "ɔ", "ʊ"}
        return (
            vowel_duration if phoneme.lower() in vowels else consonant_duration
        )

    def _generate_feedback(
        self,
        phoneme: str,
        accuracy: float,
        timing: float
    ) -> list[str]:
        """Generate feedback messages for articulation."""
        feedback = []

        if accuracy < settings.phoneme_confidence_threshold:
            feedback.append(f"Practice {phoneme} pronunciation more clearly")

        if timing < 0.7:
            feedback.append(
                f"Adjust timing for {phoneme} - try to be more consistent"
            )

        if accuracy > 0.9 and timing > 0.9:
            feedback.append(f"Excellent {phoneme} production!")

        return feedback if feedback else ["Good effort! Keep practicing."]


class JournalService:
    """Secure SEL journaling service with sentiment analysis."""

    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)

    def encrypt_content(self, content: str) -> str:
        """Encrypt journal content for secure storage."""
        if not content:
            return ""

        encrypted = self.cipher.encrypt(content.encode())
        return encrypted.decode()

    def decrypt_content(self, encrypted_content: str) -> str:
        """Decrypt journal content for reading."""
        if not encrypted_content:
            return ""

        try:
            decrypted = self.cipher.decrypt(encrypted_content.encode())
            return decrypted.decode()
        except Exception:  # pylint: disable=broad-exception-caught
            return "[Content could not be decrypted]"

    def analyze_sentiment(self, content: str) -> SentimentAnalysis:
        """
        Analyze sentiment of journal content.

        Args:
            content: Journal content text

        Returns:
            Sentiment analysis results
        """
        # Simple rule-based sentiment analysis
        # In production, use a proper NLP model

        positive_words = {
            "happy", "joy", "excited", "good", "great", "awesome",
            "wonderful", "amazing", "love", "like", "enjoy", "fun",
            "success", "proud", "confident", "grateful", "thankful"
        }

        negative_words = {
            "sad", "angry", "upset", "bad", "terrible", "awful",
            "hate", "dislike", "frustrated", "worried", "anxious",
            "scared", "afraid", "disappointed", "lonely", "stressed"
        }

        neutral_words = {
            "okay", "fine", "normal", "usual", "regular", "average",
            "nothing", "same", "typical", "ordinary"
        }

        # Tokenize and analyze
        words = re.findall(r"\b\w+\b", content.lower())

        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        neutral_count = sum(1 for word in words if word in neutral_words)

        total_sentiment_words = positive_count + negative_count + neutral_count

        if total_sentiment_words == 0:
            # Default to neutral if no sentiment words found
            positive_score = 0.33
            negative_score = 0.33
            neutral_score = 0.34
            sentiment = SentimentType.NEUTRAL
        else:
            positive_score = positive_count / total_sentiment_words
            negative_score = negative_count / total_sentiment_words
            neutral_score = neutral_count / total_sentiment_words

            # Determine overall sentiment
            if (
                positive_score > negative_score
                and positive_score > neutral_score
            ):
                sentiment = SentimentType.POSITIVE
            elif (
                negative_score > positive_score
                and negative_score > neutral_score
            ):
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL

        # Calculate confidence based on the strength of sentiment
        max_score = max(positive_score, negative_score, neutral_score)
        confidence = max_score

        # Extract key emotions
        emotions_found = []
        for word in words:
            if word in positive_words or word in negative_words:
                emotions_found.append(word)

        key_emotions = list(set(emotions_found))[:5]  # Limit to 5 emotions

        return SentimentAnalysis(
            sentiment=sentiment,
            confidence=confidence,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            key_emotions=key_emotions
        )

    def should_trigger_alert(self, sentiment: SentimentAnalysis) -> bool:
        """
        Check if sentiment analysis should trigger an alert.

        Args:
            sentiment: Sentiment analysis results

        Returns:
            True if alert should be triggered
        """
        # Trigger alert for strong negative sentiment
        return (
            sentiment.sentiment == SentimentType.NEGATIVE and
            sentiment.confidence > 0.8 and
            sentiment.negative_score > 0.7
        )

    def get_privacy_level_access(
        self,
        privacy_level: PrivacyLevel,
        requester_role: str
    ) -> bool:
        """
        Check if requester has access to content with given privacy level.

        Args:
            privacy_level: Content privacy level
            requester_role: Role of the requester

        Returns:
            True if access is allowed
        """
        access_matrix = {
            PrivacyLevel.PRIVATE: ["student"],
            PrivacyLevel.THERAPIST_ONLY: ["student", "therapist"],
            PrivacyLevel.TEAM_SHARED: [
                "student", "teacher", "counselor", "therapist"
            ]
        }

        return requester_role in access_matrix.get(privacy_level, [])

    def clean_expired_entries(self, retention_days: int = None) -> int:
        """
        Clean up expired journal entries based on retention policy.

        Args:
            retention_days: Days to retain entries (uses config default)

        Returns:
            Number of entries cleaned up
        """
        if retention_days is None:
            retention_days = settings.journal_retention_days

        # Calculate cutoff date for retention policy
        _ = datetime.utcnow() - timedelta(days=retention_days)

        # TODO: Implement actual database cleanup  # pylint: disable=fixme
        # This would typically involve:
        # 1. Query for entries older than cutoff_date
        # 2. Safely delete entries while preserving analytics
        # 3. Log cleanup operations for audit

        return 0  # Placeholder


# Initialize service instances
speech_processor = SpeechProcessor()
journal_service = JournalService()
