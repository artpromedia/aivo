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
    SentimentAnalysis,
    SentimentType,
)

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
        # TODO: Implement actual speech processing with librosa/soundfile
        # For now, return mock data
        mock_phonemes = [
            PhonemeTimingData(
                phoneme="p",
                start_time=0.0,
                end_time=0.15,
                confidence=0.85,
                expected_phoneme="p"
            ),
            PhonemeTimingData(
                phoneme="æ",
                start_time=0.15,
                end_time=0.35,
                confidence=0.92,
                expected_phoneme="æ"
            ),
        ]
        return mock_phonemes
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
    scores = []
    for phoneme in phoneme_data:
        # TODO: Implement actual scoring algorithm
        # For now, return mock scores based on confidence
        base_score = phoneme.confidence
        score = ArticulationScore(
            phoneme=phoneme.phoneme,
            accuracy_score=base_score,
            timing_score=min(base_score + 0.1, 1.0),
            consistency_score=max(base_score - 0.05, 0.0),
            fluency_score=base_score,
            overall_score=base_score,
            feedback=["Good pronunciation"] if base_score > 0.8 else [
                "Try to articulate more clearly"
            ]
        )
        scores.append(score)

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
    # TODO: Implement actual session creation with database storage

    session = DrillSession(
        student_id=student_id,
        drill_type=DrillType.PHONEME,
        target_phonemes=target_phonemes,
        articulation_level=ArticulationLevel.BEGINNER,
        scores=[],
        notes=""
    )

    return session


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

    # TODO: Implement sentiment analysis
    # For now, return mock sentiment data

    sentiment = SentimentAnalysis(
        sentiment=SentimentType.POSITIVE,
        confidence=0.85,
        positive_score=0.7,
        negative_score=0.1,
        neutral_score=0.2,
        key_emotions=["happy", "excited"]
    )

    # Calculate word count and reading time
    word_count = len(entry_request.content.split())
    reading_time = word_count / 200.0  # Assume 200 WPM reading speed

    return JournalEntryResponse(
        entry=entry,
        sentiment_analysis=sentiment,
        word_count=word_count,
        reading_time_minutes=reading_time
    )


@app.get(
    "/journal/entries/{student_id}",
    response_model=JournalHistoryResponse
)
async def get_journal_history(
    _student_id: UUID,
    _history_request: JournalHistoryRequest = Depends(),
):
    """
    Get journal history for a student.

    Args:
        student_id: Student identifier
        history_request: History filtering parameters

    Returns:
        Paginated journal history
    """
    # TODO: Implement actual database query
    # For now, return empty response
    return JournalHistoryResponse(
        entries=[],
        total_count=0,
        page_count=0,
        current_page=0
    )


@app.get("/journal/entries/{student_id}/{entry_id}")
async def get_journal_entry(
    _student_id: UUID,
    _entry_id: UUID,
):
    """
    Get a specific journal entry.

    Args:
        student_id: Student identifier
        entry_id: Entry identifier

    Returns:
        Journal entry details
    """
    # TODO: Implement actual database query with privacy checks
    raise HTTPException(status_code=404, detail="Entry not found")


@app.delete("/journal/entries/{student_id}/{entry_id}")
async def delete_journal_entry(
    _student_id: UUID,
    _entry_id: UUID,
):
    """
    Delete a journal entry.

    Args:
        student_id: Student identifier
        entry_id: Entry identifier

    Returns:
        Deletion confirmation
    """
    # TODO: Implement actual deletion with privacy checks
    return {"message": "Entry deleted successfully"}


# Admin and Analytics Endpoints

@app.get("/admin/speech-analytics")
async def get_speech_analytics():
    """Get speech therapy analytics and progress reports."""
    # TODO: Implement analytics aggregation
    return {
        "total_sessions": 0,
        "average_improvement": 0.0,
        "common_challenges": []
    }


@app.get("/admin/journal-analytics")
async def get_journal_analytics():
    """Get SEL journaling analytics and insights."""
    # TODO: Implement journal analytics
    return {
        "total_entries": 0,
        "sentiment_trends": {},
        "engagement_metrics": {}
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
