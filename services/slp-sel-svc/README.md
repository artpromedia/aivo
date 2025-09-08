# SLP/SEL Engine Service

## Overview

The **SLP/SEL Engine** service provides speech language pathology (SLP) and
social emotional learning (SEL) capabilities for educational platforms. This
service offers speech articulation analysis and secure journaling features for
therapeutic and educational use.

## Features

### Speech Language Pathology (SLP)

- **Phoneme Timing Analysis**: Extract phoneme-level timing data from audio recordings
- **Articulation Scoring**: Automated scoring of speech articulation quality
- **Speech Drill Management**: Create and track speech therapy practice sessions
- **Progress Tracking**: Monitor improvement across articulation exercises

### Social Emotional Learning (SEL)

- **Secure Journaling**: Encrypted journal entries with configurable privacy levels
- **Sentiment Analysis**: Automated analysis of emotional content in journal entries
- **Privacy Controls**: Multi-level privacy settings (private, therapist-only, team-shared)
- **Alert System**: Automatic detection of concerning emotional patterns

## API Endpoints

### Speech Processing

- `POST /speech/analyze-phonemes` - Analyze audio for phoneme timing
- `POST /speech/score-articulation` - Score articulation quality
- `POST /speech/drill-session` - Create speech drill session

### SEL Journaling

- `POST /journal/entries` - Create journal entry with sentiment analysis
- `GET /journal/entries/{student_id}` - Get journal history
- `GET /journal/entries/{student_id}/{entry_id}` - Get specific entry
- `DELETE /journal/entries/{student_id}/{entry_id}` - Delete entry

### Administration

- `GET /admin/speech-analytics` - Speech therapy analytics
- `GET /admin/journal-analytics` - Journal analytics and insights
- `GET /health` - Service health check

## Configuration

The service uses environment variables for configuration:

### Audio Processing

- `AUDIO_SAMPLE_RATE`: Sample rate for audio processing (default: 16000)
- `PHONEME_CONFIDENCE_THRESHOLD`: Minimum confidence for phoneme detection
  (default: 0.7)

### Articulation Scoring Weights

- `ACCURACY_WEIGHT`: Weight for accuracy score (default: 0.4)
- `TIMING_WEIGHT`: Weight for timing score (default: 0.3)
- `CONSISTENCY_WEIGHT`: Weight for consistency score (default: 0.2)
- `FLUENCY_WEIGHT`: Weight for fluency score (default: 0.1)

### SEL Journaling

- `ENABLE_SENTIMENT_ANALYSIS`: Enable sentiment analysis (default: true)
- `JOURNAL_RETENTION_DAYS`: Days to retain journal entries (default: 365)
- `PRIVACY_ENCRYPTION_ENABLED`: Enable content encryption (default: true)

## Dependencies

### Audio Processing

- `librosa`: Audio analysis and feature extraction
- `soundfile`: Audio file I/O
- `scipy`: Scientific computing for signal processing
- `numpy`: Numerical computations

### Security & Privacy

- `cryptography`: Encryption for secure journaling
- `python-jose[cryptography]`: JWT token handling

### Web Framework

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation

## Installation

1. Install dependencies:

```bash
poetry install
```

1. Set environment variables in `.env` file

2. Run the service:

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Speech Processing Pipeline

1. **Audio Input**: Upload audio file via REST API
2. **Feature Extraction**: Extract MFCC features and timing data using librosa
3. **Phoneme Detection**: Identify phonemes and their temporal boundaries
4. **Articulation Scoring**: Calculate accuracy, timing, consistency, and
   fluency scores
5. **Feedback Generation**: Provide targeted feedback for improvement

## Privacy & Security

### Journal Entry Privacy Levels

- **Private**: Only accessible by the student
- **Therapist Only**: Accessible by student and assigned therapist
- **Team Shared**: Accessible by student, therapist, teachers, and counselors

### Data Protection

- All journal content is encrypted at rest using Fernet encryption
- Sentiment analysis is performed on decrypted content in memory only
- Automatic cleanup of expired entries based on retention policy
- Access control enforced at API level

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
poetry run ruff check .
poetry run black .
```

### API Documentation

When running the service, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

This service is part of the monorepo educational platform.
