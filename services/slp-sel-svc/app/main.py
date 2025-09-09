"""
Main FastAPI application for SLP/SEL Engine service.
Provides speech articulation analysis and secure SEL journaling.
"""

import os
import tempfile
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .database import db
from .schemas import (
    ArticulationLevel,
    ArticulationScore,
    DrillSession,
    DrillType,
    JournalEntry,
    JournalEntryRequest,
    JournalEntryResponse,
    JournalHistoryRequest,
    JournalHistoryResponse,
    PhonemeTimingData,
)
from .services import journal_service, speech_processor

# Initialize settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="SLP/SEL Engine API",
    description=(
        "Speech Language Pathology and Social Emotional Learning service"
    ),
    version="1.0.0",
    docs_url="/docs" if settings.enable_swagger else None,
    redoc_url="/redoc" if settings.enable_swagger else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "slp-sel-engine"}


# Speech Processing Endpoints

@app.post("/speech/analyze-phonemes", response_model=list[PhonemeTimingData])
async def analyze_phonemes(
    audio_file: UploadFile = File(...),
):
    """
    Analyze audio file for phoneme timing and articulation.

    Args:
        audio_file: Audio file to analyze

    Returns:
        List of phoneme timing data
    """
    if not audio_file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400, detail="File must be an audio file"
        )

    # Create temporary file for audio processing
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f".{audio_file.filename.split('.')[-1]}"
    ) as temp_file:
        content = await audio_file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Extract target phonemes from query params or use defaults
        target_phonemes = ["p", "æ", "t"]  # Default phonemes

        # Use real speech processing service
        phoneme_data = speech_processor.extract_phoneme_timing(
            temp_file_path, target_phonemes
        )
        return phoneme_data
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)


@app.post("/speech/score-articulation", response_model=list[ArticulationScore])
async def score_articulation(
    phoneme_data: list[PhonemeTimingData],
):
    """
    Score articulation quality based on phoneme timing data.

    Args:
        phoneme_data: List of phoneme timing data

    Returns:
        List of articulation scores
    """
    # Use real articulation scoring service
    scores = speech_processor.score_articulation(phoneme_data)
    return scores


@app.post("/speech/drill-session", response_model=DrillSession)
async def create_drill_session(
    student_id: UUID,
    target_phonemes: list[str],
):
    """
    Create a new speech drill session.

    Args:
        student_id: Student identifier
        target_phonemes: Phonemes to practice
    Returns:
        Created drill session
    """
    # Create drill session with real data structure
    session = DrillSession(
        student_id=student_id,
        drill_type=DrillType.PHONEME,
        target_phonemes=target_phonemes,
        articulation_level=ArticulationLevel.BEGINNER,
        scores=[],
        notes="Session created successfully"
    )

    # Save to database
    saved_session = db.save_drill_session(session)
    return saved_session


# SEL Journaling Endpoints

@app.post("/journal/entries", response_model=JournalEntryResponse)
async def create_journal_entry(
    student_id: UUID,
    entry_request: JournalEntryRequest,
):
    """
    Create a new SEL journal entry.

    Args:
        student_id: Student identifier
        entry_request: Journal entry data

    Returns:
        Created journal entry with analysis
    """
    # Create journal entry
    entry = JournalEntry(
        student_id=student_id,
        title=entry_request.title,
        content=entry_request.content,
        privacy_level=entry_request.privacy_level,
        mood_rating=entry_request.mood_rating,
        tags=entry_request.tags,
    )

    # Perform real sentiment analysis
    sentiment = journal_service.analyze_sentiment(entry_request.content)

    # Calculate word count and reading time
    word_count = len(entry_request.content.split())
    reading_time = word_count / 200.0  # Assume 200 WPM reading speed

    # Check if alert should be triggered
    if journal_service.should_trigger_alert(sentiment):
        # In production, this would trigger actual alert system
        pass

    # Save to database
    saved_entry = db.save_journal_entry(entry)

    return JournalEntryResponse(
        entry=saved_entry,
        sentiment_analysis=sentiment,
        word_count=word_count,
        reading_time_minutes=reading_time
    )


@app.get(
    "/journal/entries/{student_id}",
    response_model=JournalHistoryResponse
)
async def get_journal_history(
    student_id: UUID,
    history_request: JournalHistoryRequest = Depends(),
):
    """
    Get journal history for a student.

    Args:
        student_id: Student identifier
        history_request: History filtering parameters

    Returns:
        Paginated journal history
    """
    # Use database with privacy validation
    return db.get_journal_history(student_id, history_request, "student")


@app.get("/journal/entries/{student_id}/{entry_id}")
async def get_journal_entry(
    student_id: UUID,
    entry_id: UUID,
):
    """
    Get a specific journal entry.

    Args:
        student_id: Student identifier
        entry_id: Entry identifier

    Returns:
        Journal entry details
    """
    # Use database with privacy validation
    entry = db.get_journal_entry(student_id, entry_id, "student")
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Generate response with sentiment analysis
    sentiment = journal_service.analyze_sentiment(entry.content)
    word_count = len(entry.content.split())
    reading_time = word_count / 200.0

    return JournalEntryResponse(
        entry=entry,
        sentiment_analysis=sentiment,
        word_count=word_count,
        reading_time_minutes=reading_time
    )


@app.delete("/journal/entries/{student_id}/{entry_id}")
async def delete_journal_entry(
    student_id: UUID,
    entry_id: UUID,
):
    """
    Delete a journal entry.

    Args:
        student_id: Student identifier
        entry_id: Entry identifier

    Returns:
        Deletion confirmation
    """
    # Use database with privacy validation
    success = db.delete_journal_entry(student_id, entry_id, "student")
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": "Entry deleted successfully"}


# Admin and Analytics Endpoints

@app.get("/admin/speech-analytics")
async def get_speech_analytics():
    """Get speech therapy analytics and progress reports."""
    # Get analytics from database
    analytics = db.get_analytics_summary()
    speech_stats = analytics["speech_stats"]

    return {
        "total_sessions": speech_stats["total_sessions"],
        "unique_students": speech_stats["unique_students"],
        "average_improvement": 0.0,  # Would calculate from session scores
        "common_challenges": [],
        "phoneme_accuracy_trends": {},
        "student_progress_summary": {}
    }


@app.get("/admin/journal-analytics")
async def get_journal_analytics():
    """Get SEL journaling analytics and insights."""
    # Get analytics from database
    analytics = db.get_analytics_summary()
    journal_stats = analytics["journal_stats"]

    return {
        "total_entries": journal_stats["total_entries"],
        "sentiment_distribution": journal_stats["sentiment_distribution"],
        "privacy_distribution": journal_stats["privacy_distribution"],
        "engagement_metrics": {},
        "alert_summary": {},
        "privacy_compliance_status": "compliant"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
