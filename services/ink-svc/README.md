# Ink Capture Service

Digital ink capture service for stylus and finger input. Captures strokes, stores NDJSON pages in S3, and emits recognition events.

## Features

- **Stroke Capture**: Process digital ink strokes from stylus/finger input
- **Consent Gate**: Validate learner consent and permissions  
- **Media Gate**: Apply content filtering and validation policies
- **S3 Storage**: Store ink pages as NDJSON for recognition processing
- **Event Publishing**: Emit INK_READY events to trigger recognition jobs
- **Session Management**: Track drawing sessions and page counts

## API Endpoints

### POST `/strokes`

Submit digital ink strokes for processing.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "learner_id": "550e8400-e29b-41d4-a716-446655440002", 
  "subject": "mathematics",
  "page_number": 1,
  "canvas_width": 800,
  "canvas_height": 600,
  "strokes": [
    {
      "stroke_id": "550e8400-e29b-41d4-a716-446655440003",
      "tool_type": "pen",
      "color": "#000000", 
      "width": 2.0,
      "points": [
        {"x": 100, "y": 150, "pressure": 0.8, "timestamp": 0},
        {"x": 105, "y": 152, "pressure": 0.9, "timestamp": 16}
      ]
    }
  ],
  "metadata": {"device": "tablet"}
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "page_id": "550e8400-e29b-41d4-a716-446655440004",
  "s3_key": "ink-pages/2025/09/08/learner_550e8400-e29b-41d4-a716-446655440002/session_550e8400-e29b-41d4-a716-446655440001/page_550e8400-e29b-41d4-a716-446655440004.ndjson",
  "stroke_count": 1,
  "recognition_job_id": "550e8400-e29b-41d4-a716-446655440005",
  "created_at": "2025-09-08T10:30:00Z"
}
```

### GET `/sessions/{sessionId}/status`

Get status information for an ink capture session.

### GET `/healthz`

Health check endpoint.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL database connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/ink_db` |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 storage | |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 storage | |
| `AWS_REGION` | AWS region for S3 bucket | `us-east-1` |
| `S3_BUCKET_NAME` | S3 bucket name for ink storage | `aivo-ink-storage` |
| `EVENT_SERVICE_URL` | URL for event publishing service | `http://localhost:8080/events` |
| `ENABLE_CONSENT_GATE` | Enable consent validation | `true` |
| `ENABLE_MEDIA_GATE` | Enable media policy validation | `true` |

## Development

### Setup

```bash
# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
poetry run python -m app.main
```

### Testing

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app
```

### Docker

```bash
# Build image
docker build -t ink-svc .

# Run container
docker run -p 8000:8000 --env-file .env ink-svc
```

## Architecture

The service follows a layered architecture:

- **API Layer** (`main.py`): FastAPI endpoints and request/response handling
- **Service Layer** (`services.py`): Business logic and external integrations
- **Data Layer** (`models.py`, `database.py`): Database models and persistence
- **Schema Layer** (`schemas.py`): Request/response models and validation

## Event Flow

1. Client submits ink strokes via POST `/strokes`
2. Service validates consent and media policies
3. Stroke data is stored as NDJSON in S3
4. Database records are created for tracking
5. INK_READY event is published for recognition processing
6. Response includes S3 key and recognition job ID

## Storage Format

Ink pages are stored in S3 as NDJSON with the following structure:

```json
{
  "page_id": "550e8400-e29b-41d4-a716-446655440004",
  "session_id": "550e8400-e29b-41d4-a716-446655440001", 
  "learner_id": "550e8400-e29b-41d4-a716-446655440002",
  "subject": "mathematics",
  "page_number": 1,
  "canvas_width": 800,
  "canvas_height": 600,
  "strokes": [...],
  "created_at": "2025-09-08T10:30:00Z",
  "metadata": {}
}
```
