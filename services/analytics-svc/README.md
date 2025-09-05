# Analytics Service

REST API for learning analytics over Snowflake with differential privacy.

## Features

- **Tenant-scoped metrics**: Summary, mastery, and streak analytics
- **Differential privacy**: Laplace noise for privacy protection  
- **Response caching**: 30-second TTL for performance
- **OpenTelemetry**: Distributed tracing with Jaeger
- **Snowflake integration**: Analytics over data warehouse

## API Endpoints

### GET /metrics/summary

Get overall learning metrics for a tenant.

**Query Parameters:**

- `tenant_id` (required): Tenant identifier
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Response:**

```json
{
  "data": {
    "total_learners": 1250,
    "active_learners_today": 89,
    "active_learners_week": 567,
    "total_sessions": 8934,
    "avg_session_duration_minutes": 24.5,
    "total_correct_answers": 67832,
    "total_incorrect_answers": 12456,
    "overall_accuracy": 84.5,
    "concepts_mastered": 234,
    "avg_mastery_score": 0.78
  },
  "tenant_id": "tenant_123",
  "generated_at": "2024-01-15T10:30:00Z",
  "cache_hit": false
}
```

### GET /metrics/mastery

Get mastery progression metrics for learners.

**Query Parameters:**

- `tenant_id` (required): Tenant identifier
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Max results (default: 100, max: 1000)

### GET /metrics/streaks

Get learning streak metrics for learners.

**Query Parameters:**

- `tenant_id` (required): Tenant identifier
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `limit` (optional): Max results (default: 100, max: 1000)

## Configuration

Set environment variables:

```bash
# Snowflake connection
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=AIVO_ANALYTICS
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN

# Differential privacy
DP_EPSILON=1.0
DP_SENSITIVITY=1.0

# OpenTelemetry
OTEL_ENDPOINT=http://jaeger:14250
```

## Development

```bash
# Install dependencies
poetry install

# Run service
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
poetry run pytest

# Format code
poetry run ruff check --fix
```

## Docker

```bash
# Build image
docker build -t analytics-svc .

# Run container
docker run -p 8000:8000 \
  -e SNOWFLAKE_ACCOUNT=your_account \
  -e SNOWFLAKE_USER=your_user \
  -e SNOWFLAKE_PASSWORD=your_password \
  analytics-svc
```
