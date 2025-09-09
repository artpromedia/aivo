"""
In-memory database service for development and testing.
In production, this would be replaced with proper database integration.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from .schemas import (
    DrillSession,
    JournalEntry,
    JournalEntryResponse,
    JournalHistoryRequest,
    JournalHistoryResponse,
    PrivacyLevel,
)
from .services import journal_service


class InMemoryDatabase:
    """Simple in-memory database for development."""

    def __init__(self):
        self.journal_entries: dict[UUID, JournalEntry] = {}
        self.drill_sessions: dict[UUID, DrillSession] = {}
        self.student_entries: dict[UUID, list[UUID]] = {}  # student -> entries

    def save_journal_entry(self, entry: JournalEntry) -> JournalEntry:
        """Save a journal entry."""
        self.journal_entries[entry.entry_id] = entry

        # Index by student
        if entry.student_id not in self.student_entries:
            self.student_entries[entry.student_id] = []
        self.student_entries[entry.student_id].append(entry.entry_id)

        return entry

    def get_journal_entry(
        self, student_id: UUID, entry_id: UUID, requester_role: str = "student"
    ) -> Optional[JournalEntry]:
        """Get a specific journal entry with privacy validation."""
        entry = self.journal_entries.get(entry_id)

        if not entry or entry.student_id != student_id:
            return None

        # Check privacy permissions
        if not journal_service.get_privacy_level_access(
            entry.privacy_level, requester_role
        ):
            return None

        return entry

    def get_journal_history(
        self,
        student_id: UUID,
        request: JournalHistoryRequest,
        requester_role: str = "student",
    ) -> JournalHistoryResponse:
        """Get paginated journal history with filtering."""
        # Get all entries for student
        entry_ids = self.student_entries.get(student_id, [])
        entries = []

        for entry_id in entry_ids:
            entry = self.journal_entries.get(entry_id)
            if not entry:
                continue

            # Apply privacy filter
            if not journal_service.get_privacy_level_access(
                entry.privacy_level, requester_role
            ):
                continue

            # Apply privacy level filter
            if (
                request.privacy_levels
                and entry.privacy_level not in request.privacy_levels
            ):
                continue

            # Apply date filters
            if request.start_date and entry.created_at < request.start_date:
                continue
            if request.end_date and entry.created_at > request.end_date:
                continue

            # Apply tag filter
            if request.tags and not any(
                tag in entry.tags for tag in request.tags
            ):
                continue

            entries.append(entry)

        # Sort by creation date (newest first)
        entries.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total_count = len(entries)
        start_index = request.offset
        end_index = start_index + request.limit
        paginated_entries = entries[start_index:end_index]

        # Convert to response format
        response_entries = []
        sentiment_scores = []

        for entry in paginated_entries:
            sentiment = journal_service.analyze_sentiment(entry.content)
            word_count = len(entry.content.split())
            reading_time = word_count / 200.0

            response_entries.append(
                JournalEntryResponse(
                    entry=entry,
                    sentiment_analysis=sentiment,
                    word_count=word_count,
                    reading_time_minutes=reading_time,
                )
            )

            score_diff = sentiment.positive_score - sentiment.negative_score
            sentiment_scores.append(score_diff)

        # Calculate sentiment trends
        sentiment_trends = {}
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            if len(sentiment_scores) > 1:
                first_score = sentiment_scores[0]
                last_score = sentiment_scores[-1]
                trend = (
                    "improving" if last_score > first_score else "declining"
                )
            else:
                trend = "stable"

            sentiment_trends = {
                "average_sentiment": avg_sentiment,
                "trend_direction": trend,
                "entries_analyzed": len(sentiment_scores),
            }

        # Calculate pagination info
        page_size = request.limit
        page_count = (total_count + page_size - 1) // page_size
        current_page = request.offset // page_size
        has_more = end_index < total_count

        return JournalHistoryResponse(
            entries=response_entries,
            total_count=total_count,
            page_count=page_count,
            current_page=current_page,
            has_more=has_more,
            sentiment_trends=sentiment_trends,
        )

    def delete_journal_entry(
        self, student_id: UUID, entry_id: UUID, requester_role: str = "student"
    ) -> bool:
        """Delete a journal entry with privacy validation."""
        entry = self.get_journal_entry(student_id, entry_id, requester_role)
        if not entry:
            return False

        # Remove from main storage
        del self.journal_entries[entry_id]

        # Remove from student index
        if student_id in self.student_entries:
            self.student_entries[student_id].remove(entry_id)

        return True

    def save_drill_session(self, session: DrillSession) -> DrillSession:
        """Save a drill session."""
        self.drill_sessions[session.session_id] = session
        return session

    def get_drill_session(self, session_id: UUID) -> Optional[DrillSession]:
        """Get a specific drill session."""
        return self.drill_sessions.get(session_id)

    def get_student_drill_sessions(
        self, student_id: UUID
    ) -> list[DrillSession]:
        """Get all drill sessions for a student."""
        return [
            session
            for session in self.drill_sessions.values()
            if session.student_id == student_id
        ]

    def cleanup_expired_entries(self, retention_days: int = 365) -> int:
        """Clean up expired entries based on retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        expired_entries = []

        for entry_id, entry in self.journal_entries.items():
            if entry.created_at < cutoff_date:
                expired_entries.append(entry_id)

        for entry_id in expired_entries:
            entry = self.journal_entries[entry_id]
            student_id = entry.student_id

            # Remove from main storage
            del self.journal_entries[entry_id]

            # Remove from student index
            if student_id in self.student_entries:
                self.student_entries[student_id].remove(entry_id)

        return len(expired_entries)

    def get_analytics_summary(self) -> dict:
        """Get analytics summary for admin endpoints."""
        total_entries = len(self.journal_entries)
        total_sessions = len(self.drill_sessions)

        # Calculate sentiment distribution
        sentiment_counts = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "mixed": 0,
        }

        for entry in self.journal_entries.values():
            sentiment = journal_service.analyze_sentiment(entry.content)
            sentiment_counts[sentiment.sentiment.value] += 1

        return {
            "journal_stats": {
                "total_entries": total_entries,
                "sentiment_distribution": sentiment_counts,
                "privacy_distribution": {
                    level.value: sum(
                        1
                        for e in self.journal_entries.values()
                        if e.privacy_level == level
                    )
                    for level in PrivacyLevel
                },
            },
            "speech_stats": {
                "total_sessions": total_sessions,
                "unique_students": len(
                    set(s.student_id for s in self.drill_sessions.values())
                ),
            },
        }


# Global database instance
db = InMemoryDatabase()
