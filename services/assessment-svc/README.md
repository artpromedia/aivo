# Assessment Service

A baseline assessment service that evaluates user knowledge levels (L0-L4)
across different subjects using adaptive questioning.

## Features

- **Adaptive Assessment Algorithm**: Uses confidence-based convergence to
  determine user level in 5-7 questions
- **Multi-Subject Support**: Mathematics, Science, English, History, Geography
- **L0-L4 Level Assessment**: Comprehensive level determination from beginner
  to advanced
- **Event Publishing**: Emits BASELINE_COMPLETE and other assessment events
- **Session Management**: Time-based session handling with expiration
- **RESTful API**: FastAPI-based with comprehensive validation

## API Endpoints

### Assessment Workflow

1. **Start Assessment**: `POST /baseline/start`

   ```json
   {
     "user_id": "user123",
     "subject": "mathematics"
   }
   ```

2. **Submit Answer**: `POST /baseline/answer`

   ```json
   {
     "session_id": "sess_123",
     "question_id": "q1",
     "answer": "A"
   }
   ```

3. **Get Report**: `GET /baseline/report?sessionId=sess_123`

### Additional Endpoints

- **Health Check**: `GET /health`
- **Session Status**: `GET /sessions/{session_id}/status`
- **API Documentation**: `GET /docs`

## Installation

1. **Install Dependencies**:

   ```bash
   cd services/assessment-svc
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the Service**:

   ```bash
   python run.py
   # Or with custom settings:
   python run.py --host 0.0.0.0 --port 8001 --reload
   ```

4. **Run Tests**:

   ```bash
   python -m pytest tests/ -v
   ```

## Configuration

Environment variables (see `.env.example`):

- `HOST`: Server host (default: localhost)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: false)
- `LOG_LEVEL`: Logging level (default: INFO)
- `MIN_QUESTIONS`: Minimum questions per assessment (default: 5)
- `MAX_QUESTIONS`: Maximum questions per assessment (default: 7)
- `CONFIDENCE_THRESHOLD`: Convergence confidence threshold (default: 0.8)
- `SESSION_TIMEOUT_MINUTES`: Session expiration time (default: 60)
- `EVENT_ENDPOINT`: Event publishing endpoint
- `EVENT_TIMEOUT`: Event publishing timeout

## Assessment Algorithm

The service uses an adaptive assessment algorithm that:

1. **Starts at L2**: Initial level estimate
2. **Adjusts Based on Performance**: Moves up/down based on correct/incorrect answers
3. **Tracks Confidence**: Increases confidence with consistent performance
4. **Converges**: Completes when confidence threshold is reached (5-7 questions)
5. **Emits Events**: Publishes BASELINE_COMPLETE event with final assessment

### Level Definitions

- **L0**: Basic/Foundational level
- **L1**: Elementary level  
- **L2**: Intermediate level
- **L3**: Advanced level
- **L4**: Expert level

## Events

The service publishes events for:

- **SESSION_STARTED**: When assessment begins
- **QUESTION_ANSWERED**: After each question response
- **BASELINE_COMPLETE**: When assessment completes

### Event Payload Example

```json
{
  "event_type": "BASELINE_COMPLETE",
  "event_id": "evt_123",
  "timestamp": "2025-01-02T10:15:00Z",
  "session_id": "sess_123",
  "user_id": "user123",
  "data": {
    "subject": "mathematics",
    "level": "L2",
    "confidence": 0.85,
    "questions_answered": 6,
    "correct_answers": 4
  }
}
```

## Development

### Project Structure

```text
assessment-svc/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── enums.py             # Enums (SubjectType, LevelType, etc.)
│   ├── schemas.py           # Pydantic models
│   ├── assessment_engine.py # Core assessment logic
│   └── event_service.py     # Event publishing
├── tests/
│   ├── __init__.py
│   └── test_assessment.py   # Comprehensive test suite
├── pyproject.toml           # Poetry configuration
├── requirements.txt         # Pip requirements
├── .env.example            # Environment variables template
├── run.py                  # Startup script
└── README.md               # This file
```

### Testing

The test suite includes:

- ✅ Complete assessment workflow (start → answer → report)
- ✅ 5-7 question convergence verification
- ✅ Event publishing validation
- ✅ Error handling scenarios
- ✅ Session management
- ✅ Level estimation accuracy
- ✅ API endpoint validation

Run tests with coverage:

```bash
python -m pytest tests/ -v --cov=app --cov-report=html
```

## License

See the main project LICENSE file.
