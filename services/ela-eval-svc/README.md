# ELA Evaluator Service

A FastAPI-based service for evaluating English Language Arts (ELA) writing
submissions using rubric-based scoring with PII moderation and content safety
features.

## Features

### Core Functionality

- **Rubric-based Scoring**: Evaluates writing against standard ELA criteria
- **Grade Band Support**: Supports K-2, 3-5, 6-8, and 9-12 grade bands
- **AI-Powered Assessment**: Uses machine learning for consistent scoring
- **Teacher Notes Generation**: Provides detailed feedback and suggestions

### Safety & Privacy

- **PII Detection**: Automatically detects and anonymizes personal information
- **Content Moderation**: Filters inappropriate content
- **Privacy-First**: Processes anonymized text for scoring

### Rubric Criteria

- Ideas and Content
- Organization
- Voice
- Word Choice
- Sentence Fluency
- Conventions

## API Endpoints

### Health Check

```http
GET /health
```

### Evaluate Submission

```http
POST /evaluate
```

Evaluates a writing submission using rubric criteria.

**Request Body:**

```json
{
  "prompt": "Write about your favorite season...",
  "submission": "I love summer because...",
  "grade_band": "3-5",
  "criteria": ["ideas_and_content", "organization"],
  "enable_pii_detection": true,
  "enable_content_moderation": true
}
```

**Response:**

```json
{
  "evaluation_id": "uuid",
  "scores": [
    {
      "criterion": "ideas_and_content",
      "score": 3,
      "reasoning": "Student demonstrates...",
      "strengths": ["Clear topic", "Good examples"],
      "areas_for_improvement": ["Add more details"]
    }
  ],
  "overall_score": 3.2,
  "grade_band": "3-5",
  "pii_detected": false,
  "content_flags": [],
  "is_safe": true,
  "teacher_notes": "Student shows good understanding...",
  "suggested_next_steps": ["Practice with graphic organizers"],
  "processing_time_ms": 1250,
  "model_used": "gpt-4-turbo-preview"
}
```

### Get Evaluation History

```http
GET /evaluations
```

Retrieves evaluation history with filtering options.

### Get Specific Evaluation

```http
GET /evaluations/{evaluation_id}
```

## Grade Bands

- **K-2**: Kindergarten through 2nd grade
- **3-5**: 3rd through 5th grade  
- **6-8**: 6th through 8th grade
- **9-12**: 9th through 12th grade

## Scoring Scale

All criteria use a 4-point scale:

1. **Beginning (1)**: Minimal understanding/skill demonstrated
2. **Developing (2)**: Basic understanding/skill demonstrated  
3. **Proficient (3)**: Grade-level understanding/skill demonstrated
4. **Advanced (4)**: Above grade-level understanding/skill demonstrated

## Configuration

Key environment variables:

```bash
# Service Configuration
SERVICE_NAME=ela-eval-svc
SERVICE_VERSION=0.1.0
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ela_eval

# AI Models
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
DEFAULT_MODEL=gpt-4-turbo-preview

# Safety Settings
ENABLE_PII_DETECTION=true
ENABLE_CONTENT_MODERATION=true
PII_CONFIDENCE_THRESHOLD=0.8

# Limits
MAX_SUBMISSION_LENGTH=10000
SCORING_TIMEOUT_SECONDS=30
```

## Development

### Setup

```bash
cd services/ela-eval-svc
poetry install
```

### Run Service

```bash
poetry run python -m uvicorn app.main:app --reload --port 8000
```

### Run Tests

```bash
poetry run pytest
```

### Code Quality

```bash
poetry run black .
poetry run isort .
poetry run ruff check .
poetry run mypy .
```

## Dependencies

### Core Dependencies

- FastAPI & Uvicorn for web framework
- Pydantic for data validation
- SQLAlchemy & Alembic for database
- Redis for caching

### AI & NLP

- OpenAI & Anthropic APIs for rubric scoring
- NLTK & spaCy for text processing
- Textstat for readability analysis

### Safety & Privacy

- Presidio for PII detection and anonymization
- Custom content moderation filters

## Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│ Evaluator Svc   │────│   AI Models     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   PII Engine    │    │ Content Filter  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Security Considerations

- All PII is detected and anonymized before AI processing
- Content moderation prevents inappropriate submissions
- Evaluation data is stored securely with proper access controls
- Rate limiting and authentication recommended for production

## Monitoring

Key metrics to monitor:

- Evaluation request rate and latency
- AI model response times
- PII detection accuracy
- Content moderation effectiveness
- Error rates by grade band and criteria
