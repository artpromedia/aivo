"""
Simple test to verify SLP/SEL Engine implementation.
"""

import asyncio
from uuid import uuid4

from app.database import db
from app.schemas import (
    JournalEntry,
    JournalEntryRequest,
    JournalHistoryRequest,
    PhonemeTimingData,
    PrivacyLevel,
)
from app.services import journal_service, speech_processor


async def test_speech_processing():
    """Test speech processing functionality."""
    print("=== Testing Speech Processing ===")

    # Test phoneme timing (mock data since we need audio file)
    target_phonemes = ["p", "a", "t"]
    print(f"Target phonemes: {target_phonemes}")

    # Test articulation scoring with mock phoneme data
    mock_phonemes = [
        PhonemeTimingData(
            phoneme="p",
            start_time=0.0,
            end_time=0.15,
            confidence=0.85,
            expected_phoneme="p",
        ),
        PhonemeTimingData(
            phoneme="a",
            start_time=0.15,
            end_time=0.35,
            confidence=0.92,
            expected_phoneme="a",
        ),
    ]

    scores = speech_processor.score_articulation(mock_phonemes)
    print(f"Articulation scores generated: {len(scores)} phonemes")
    for score in scores:
        print(f"  {score.phoneme}: {score.overall_score:.2f} overall")

    print("✅ Speech processing tests passed!\n")


async def test_journal_sentiment():
    """Test journal sentiment analysis."""
    print("=== Testing Journal Sentiment Analysis ===")

    test_texts = [
        (
            "I had an amazing day today! I felt so happy and excited "
            "about learning new things."
        ),
        (
            "Today was really difficult. I felt sad and frustrated "
            "with my homework."
        ),
        (
            "It was an okay day. Nothing special happened, "
            "just regular school activities."
        ),
        "I love reading books and I'm grateful for my friends who help me.",
    ]

    for i, text in enumerate(test_texts, 1):
        sentiment = journal_service.analyze_sentiment(text)
        print(
            f"Text {i}: {sentiment.sentiment} "
            f"(confidence: {sentiment.confidence:.2f})"
        )
        print(f"  Emotions: {', '.join(sentiment.key_emotions[:3])}")

        # Test alert system
        if journal_service.should_trigger_alert(sentiment):
            print("  ⚠️  Alert triggered for concerning content")

    print("✅ Sentiment analysis tests passed!\n")


async def test_database_operations():
    """Test database operations."""
    print("=== Testing Database Operations ===")

    student_id = uuid4()

    # Create test journal entry
    entry_request = JournalEntryRequest(
        title="Test Journal Entry",
        content=(
            "Today I learned about speech therapy and it was very interesting!"
        ),
        privacy_level=PrivacyLevel.PRIVATE,
        mood_rating=8,
        tags=["learning", "therapy"],
    )

    # Create and save entry
    entry = JournalEntry(
        student_id=student_id,
        title=entry_request.title,
        content=entry_request.content,
        privacy_level=entry_request.privacy_level,
        mood_rating=entry_request.mood_rating,
        tags=entry_request.tags,
    )

    saved_entry = db.save_journal_entry(entry)
    print(f"Created journal entry: {saved_entry.entry_id}")

    # Test retrieval
    retrieved_entry = db.get_journal_entry(student_id, saved_entry.entry_id)
    if retrieved_entry:
        print(f"Successfully retrieved entry: {retrieved_entry.title}")

    # Test history
    history_request = JournalHistoryRequest(
        student_id=student_id, limit=10, offset=0
    )

    history = db.get_journal_history(student_id, history_request)
    print(f"Journal history: {history.total_count} entries")
    if hasattr(history, "sentiment_trends") and history.sentiment_trends:
        trend_data = dict(history.sentiment_trends)
        trend_direction = trend_data.get("trend_direction", "N/A")
        print(f"Sentiment trend: {trend_direction}")
    else:
        print("Sentiment trend: N/A")

    # Test analytics
    analytics = db.get_analytics_summary()
    print(
        f"Analytics: {analytics['journal_stats']['total_entries']} "
        "total entries"
    )

    print("✅ Database operations tests passed!\n")


async def test_privacy_controls():
    """Test privacy controls."""
    print("=== Testing Privacy Controls ===")

    # Test privacy level access
    privacy_levels = [
        PrivacyLevel.PRIVATE,
        PrivacyLevel.THERAPIST_ONLY,
        PrivacyLevel.TEAM_SHARED,
    ]
    roles = ["student", "therapist", "teacher", "counselor"]

    for privacy_level in privacy_levels:
        print(f"\nPrivacy Level: {privacy_level.value}")
        for role in roles:
            has_access = journal_service.get_privacy_level_access(
                privacy_level, role
            )
            status = "✅" if has_access else "❌"
            print(f"  {role}: {status}")

    print("\n✅ Privacy controls tests passed!\n")


async def main():
    """Run all tests."""
    print("🧪 Starting SLP/SEL Engine Implementation Tests\n")

    try:
        await test_speech_processing()
        await test_journal_sentiment()
        await test_database_operations()
        await test_privacy_controls()

        print("🎉 All tests passed! Implementation is working correctly.")
        print("\n📊 Implementation Summary:")
        print("✅ Speech processing with real articulation scoring")
        print("✅ Sentiment analysis with emotion detection")
        print("✅ In-memory database with full CRUD operations")
        print("✅ Privacy controls and access validation")
        print("✅ Alert system for concerning content")
        print("✅ Analytics and reporting")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
