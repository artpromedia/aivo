# Problem Session Orchestrator Service

A comprehensive orchestration service that coordinates interactive learning
sessions across multiple subject-specific services including ink capture,
math recognition, and science solving.

## Overview

The Problem Session Orchestrator implements the
**plan→present→ink→recognize→grade→feedback** workflow for interactive
learning experiences. It serves as the central coordinator that integrates:

- **Subject Brain Service** - Activity planning and personalization
- **Ink Capture Service** - Digital handwriting capture
- **Math Recognition Service** - Mathematical expression recognition
- **Science Solver Service** - Scientific problem solving
- **Event System** - Analytics and progress tracking

## Features

### 🎯 Subject-Aware Orchestration

- **Multi-Subject Support**: Mathematics, Science, Physics, Chemistry, Biology
- **Intelligent Routing**: Directs recognition to appropriate services based on subject
- **Adaptive Workflow**: Customizes session flow based on subject requirements

### 📝 Interactive Learning Workflow

1. **PLAN** - Creates personalized activity plans using Subject Brain
2. **PRESENT** - Presents problems and activities to learners
3. **INK** - Captures digital handwriting from stylus/touch input
4. **RECOGNIZE** - Processes ink using subject-specific recognition services
5. **GRADE** - Evaluates responses for correctness and provides scoring
6. **FEEDBACK** - Delivers immediate feedback and progresses session

### 🔄 Real-Time Processing

- **Asynchronous Recognition** - Non-blocking ink processing
- **Live Session Updates** - Real-time status tracking
- **Performance Monitoring** - Tracks accuracy, confidence, and timing

### 📊 Analytics & Events

- **SESSION_RESULT Events** - Published for completed sessions
- **Performance Metrics** - Accuracy, confidence, duration tracking
- **Progress Analytics** - Problem attempt and success rates

## Quick Start

### Development Setup

```bash
cd services/problem-session-svc
poetry install
```

### Environment Configuration

Create `.env` file:

```env
# Service Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# External Services
INK_SERVICE_URL=http://localhost:8001
MATH_SERVICE_URL=http://localhost:8002
SCIENCE_SERVICE_URL=http://localhost:8003
SUBJECT_BRAIN_URL=http://localhost:8004
EVENT_SERVICE_URL=http://localhost:8080/events

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/problem_session_db

# Session Settings
SESSION_TIMEOUT_MINUTES=30
RECOGNITION_CONFIDENCE_THRESHOLD=0.7
```

### Running the Service

```bash
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## API Usage

### Starting a Session

```bash
curl -X POST http://localhost:8000/start \
  -H "Content-Type: application/json" \
  -d '{
    "learner_id": "550e8400-e29b-41d4-a716-446655440001",
    "subject": "mathematics",
    "session_duration_minutes": 30,
    "canvas_width": 800,
    "canvas_height": 600
  }'
```

Response:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440002",
  "learner_id": "550e8400-e29b-41d4-a716-446655440001",
  "subject": "mathematics",
  "status": "active",
  "current_phase": "present",
  "created_at": "2025-09-09T10:30:00Z",
  "ink_session_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

### Submitting Ink

```bash
curl -X POST http://localhost:8000/ink \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440002",
    "page_number": 1,
    "strokes": [
      {
        "stroke_id": "550e8400-e29b-41d4-a716-446655440004",
        "tool_type": "pen",
        "color": "#000000",
        "width": 2.0,
        "points": [
          {"x": 100, "y": 150, "pressure": 0.8, "timestamp": 0},
          {"x": 110, "y": 155, "pressure": 0.9, "timestamp": 50}
        ]
      }
    ],
    "metadata": {"device": "tablet"}
  }'
```

### Checking Session Status

```bash
curl http://localhost:8000/sessions/550e8400-e29b-41d4-a716-446655440002
```

## Architecture

### Service Integration

```mermaid
graph TD
    A[Problem Session Orchestrator] --> B[Subject Brain Service]
    A --> C[Ink Capture Service]
    A --> D[Math Recognition Service]
    A --> E[Science Solver Service]
    A --> F[Event Service]
    
    B --> G[Activity Planning]
    C --> H[Digital Ink Storage]
    D --> I[LaTeX Recognition]
    E --> J[Chemical Equations]
    F --> K[Analytics Events]
```

### Workflow States

```mermaid
stateDiagram-v2
    [*] --> PLANNING
    PLANNING --> ACTIVE: Plan Created
    ACTIVE --> WAITING_INK: Problem Presented
    WAITING_INK --> RECOGNIZING: Ink Submitted
    RECOGNIZING --> GRADING: Recognition Complete
    GRADING --> PROVIDING_FEEDBACK: Grading Complete
    PROVIDING_FEEDBACK --> WAITING_INK: Next Problem
    PROVIDING_FEEDBACK --> COMPLETED: Session Complete
    RECOGNIZING --> FAILED: Recognition Failed
    GRADING --> FAILED: Grading Failed
    COMPLETED --> [*]
    FAILED --> [*]
```

## Database Schema

### ProblemSession Table

| Column | Type | Description |
|--------|------|-------------|
| session_id | UUID | Primary key, unique session identifier |
| learner_id | UUID | Foreign key to learner |
| subject | VARCHAR(50) | Subject area (mathematics, science, etc.) |
| status | VARCHAR(30) | Current session status |
| current_phase | VARCHAR(20) | Current workflow phase |
| created_at | TIMESTAMP | Session creation time |
| started_at | TIMESTAMP | Session start time |
| completed_at | TIMESTAMP | Session completion time |
| planned_activities | JSON | Activity plan from Subject Brain |
| ink_session_id | UUID | Associated ink capture session |
| total_problems_attempted | INTEGER | Count of problems attempted |
| total_problems_correct | INTEGER | Count of correct answers |
| average_confidence | FLOAT | Average recognition confidence |

### ProblemAttempt Table

| Column | Type | Description |
|--------|------|-------------|
| attempt_id | UUID | Primary key, unique attempt identifier |
| session_id | UUID | Foreign key to problem session |
| activity_id | VARCHAR(100) | Activity identifier from plan |
| problem_type | VARCHAR(50) | Type of problem (algebraic, equation, etc.) |
| problem_statement | TEXT | The problem presented to learner |
| ink_page_id | UUID | Associated ink page |
| recognized_expression | TEXT | Recognized mathematical expression |
| recognition_confidence | FLOAT | Recognition confidence score |
| is_correct | BOOLEAN | Whether answer was correct |
| grade_score | FLOAT | Numerical grade (0.0-1.0) |
| grade_feedback | TEXT | Feedback message |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Service host address | `127.0.0.1` |
| `PORT` | Service port | `8000` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `INK_SERVICE_URL` | Ink capture service URL | `http://localhost:8001` |
| `MATH_SERVICE_URL` | Math recognition service URL | `http://localhost:8002` |
| `SCIENCE_SERVICE_URL` | Science solver service URL | `http://localhost:8003` |
| `SUBJECT_BRAIN_URL` | Subject brain service URL | `http://localhost:8004` |
| `EVENT_SERVICE_URL` | Event publishing service URL | `http://localhost:8080/events` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `SESSION_TIMEOUT_MINUTES` | Session timeout | `30` |
| `RECOGNITION_CONFIDENCE_THRESHOLD` | Minimum recognition confidence | `0.7` |
| `ENABLE_EVENTS` | Enable event publishing | `true` |

### Subject Recognition Routing

- **Mathematics** → Math Recognition Service
  - Algebraic expressions
  - Equations and inequalities
  - Calculus and derivatives
  - Geometric proofs

- **Science/Chemistry** → Science Solver Service
  - Chemical equations
  - Molecular formulas
  - Stoichiometric calculations
  - Unit conversions

- **Physics** → Science Solver Service
  - Physical equations
  - Unit analysis
  - Scientific diagrams
  - Mathematical physics

## Event Publishing

### SESSION_RESULT Event

Published when sessions complete:

```json
{
  "event_type": "SESSION_RESULT",
  "session_id": "550e8400-e29b-41d4-a716-446655440002",
  "learner_id": "550e8400-e29b-41d4-a716-446655440001",
  "subject": "mathematics",
  "status": "completed",
  "total_problems_attempted": 5,
  "total_problems_correct": 4,
  "average_confidence": 0.87,
  "session_duration_minutes": 28,
  "completed_at": "2025-09-09T11:00:30Z",
  "performance_metrics": {
    "accuracy": 0.8,
    "planned_duration": 30,
    "actual_duration": 28
  }
}
```

## Testing

### Unit Tests

```bash
poetry run pytest
```

### Integration Testing

```bash
# Start dependencies first
docker-compose up -d postgres

# Run integration tests
poetry run pytest tests/integration/
```

### Load Testing

```bash
# Test session creation
ab -n 100 -c 10 -T application/json -p session_request.json http://localhost:8000/start
```

## Monitoring

### Health Checks

- `GET /health` - Service health status
- Dependency health monitoring
- Database connection validation

### Metrics

- Session completion rates
- Recognition accuracy
- Response times
- Error rates

### Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2025-09-09T10:30:00Z",
  "level": "INFO",
  "message": "Session started successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440002",
  "learner_id": "550e8400-e29b-41d4-a716-446655440001",
  "subject": "mathematics"
}
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY app/ ./app/
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: problem-session-svc
spec:
  replicas: 3
  selector:
    matchLabels:
      app: problem-session-svc
  template:
    metadata:
      labels:
        app: problem-session-svc
    spec:
      containers:
      - name: problem-session-svc
        image: problem-session-svc:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
```

## Development

### Code Quality

```bash
# Linting
poetry run ruff check .
poetry run mypy app/

# Formatting
poetry run black app/
```

### Database Migrations

```bash
# Create migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run quality checks: `poetry run ruff check . && poetry run mypy app/`
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For technical support or questions:

- **Email**: <engineering@artpromedia.com>
- **Documentation**: `/docs`
- **API Reference**: `/docs` (when service is running)
- **Health Check**: `/health`
