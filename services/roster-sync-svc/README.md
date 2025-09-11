# Roster Sync Service

Import district rosters in 15 minutes and surface SCIM status from OneRoster, Clever, and CSV sources.

## Features

- **Multiple Connectors**: OneRoster 1.2, Clever 2.0, and CSV import support
- **Background Processing**: Celery-based async job processing with Redis
- **Progress Tracking**: Real-time sync progress with webhook notifications
- **SCIM Integration**: Track user provisioning status and sync with SCIM providers
- **Teacher/Class Linking**: Automatic enrollment and relationship mapping
- **Configurable Mappings**: External YAML/JSON field mapping configurations
- **FastAPI REST API**: Modern async API with automatic documentation

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Poetry for dependency management

### Installation

1. **Clone and setup:**
   ```bash
   cd services/roster-sync-svc
   poetry install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis settings
   ```

3. **Start services:**
   ```bash
   # Start PostgreSQL and Redis (via Docker)
   docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:14
   docker run -d --name redis -p 6379:6379 redis:7

   # Start Celery worker
   poetry run celery -A app.jobs.processor worker --loglevel=info

   # Start API server
   poetry run python -m app.main
   ```

4. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Usage

### Test Connector

```bash
curl -X POST "http://localhost:8000/connectors/test" \
  -H "Content-Type: application/json" \
  -d '{
    "connector_type": "oneroster",
    "name": "Test Config",
    "config": {
      "base_url": "https://api.school.edu/ims/oneroster/v1p2",
      "client_id": "your-client-id",
      "client_secret": "your-client-secret"
    }
  }'
```

### Start Sync Job

```bash
curl -X POST "http://localhost:8000/jobs/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "Daily Roster Sync",
    "connector_type": "oneroster",
    "connector_config": {
      "base_url": "https://api.school.edu/ims/oneroster/v1p2",
      "client_id": "your-client-id",
      "client_secret": "your-client-secret",
      "sync_users": true,
      "sync_schools": true,
      "sync_classes": true,
      "sync_enrollments": true
    },
    "district_id": "district-123",
    "webhook_url": "https://your-app.com/webhook/roster-sync"
  }'
```

### Check Job Status

```bash
curl "http://localhost:8000/jobs/{job_id}/status"
```

## Connector Configuration

### OneRoster 1.2

```yaml
# app/mappings/oneroster.yaml
connector_name: "OneRoster 1.2"
api_version: "v1p2"
authentication:
  type: "oauth2_client_credentials"
  scope: "https://purl.imsglobal.org/spec/or/v1p2/scope/roster-core.readonly"

endpoints:
  orgs:
    path: "/orgs"
    field_mappings:
      external_id: "sourcedId"
      name: "name"
      sis_id: "identifier.identifier"
```

### Clever 2.0

```json
{
  "connector_name": "Clever 2.0",
  "api_version": "v2.0",
  "authentication": {
    "type": "bearer_token"
  },
  "endpoints": {
    "districts": {
      "path": "/districts",
      "field_mappings": {
        "external_id": "id",
        "name": "name",
        "sis_id": "sis_id"
      }
    }
  }
}
```

### CSV Processing

```yaml
# app/mappings/csv.yaml
connector_name: "CSV Processor"
file_processing:
  encoding_detection: true
  chunk_size: 1000
  skip_empty_rows: true
  
format_detection:
  user_patterns:
    - columns: ["first_name", "last_name", "email", "role"]
      type: "users"
    - columns: ["student_id", "first", "last", "grade"]
      type: "students"
```

## Database Models

The service includes comprehensive SQLAlchemy 2.0 models:

- **District**: Organization/district information
- **School**: School/campus data
- **User**: Students, teachers, staff with role-based access
- **Course**: Course catalog information
- **Class**: Class sections and schedules
- **Enrollment**: User-to-class relationships
- **SyncJob**: Job tracking and status
- **SyncLog**: Detailed operation logging

## Background Jobs

Celery tasks handle async processing:

- `sync_roster_data`: Main synchronization job
- `test_connector`: Connector configuration testing
- `cleanup_old_jobs`: Maintenance and cleanup
- `send_webhook_notification`: Progress notifications

## SCIM Integration

Track user provisioning status:

```python
# User model includes SCIM fields
user.scim_status = SCIMStatus.PENDING
user.scim_id = "scim-user-id"
user.scim_last_sync = datetime.now()
```

## Development

### Code Quality

```bash
# Run linting and formatting
make py-fix

# This runs:
# poetry run ruff check --fix .
# poetry run ruff format .
```

### Testing

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app
```

### Project Structure

```
services/roster-sync-svc/
 app/
    connectors/          # Data source connectors
       base.py         # Abstract base connector
       oneroster.py    # OneRoster API connector
       clever.py       # Clever API connector
       csv.py          # CSV file processor
    jobs/               # Background job processors
       processor.py    # Celery task definitions
    mappings/           # Field mapping configurations
       oneroster.yaml  # OneRoster field mappings
       clever.json     # Clever field mappings
       csv.yaml        # CSV processing rules
    models.py           # SQLAlchemy database models
    main.py             # FastAPI application
 config/
    settings.py         # Configuration management
 Makefile                # Build and development commands
 pyproject.toml          # Poetry dependencies
 README.md
```

## Environment Variables

Key configuration options:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/roster_sync

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Connectors
ONEROSTER_TIMEOUT=30
CLEVER_RATE_LIMIT=0.2
CSV_MAX_FILE_SIZE=104857600

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
```

## Monitoring

- **Health Check**: `GET /health`
- **Celery Status**: `GET /celery/status`
- **Job Statistics**: `GET /stats/overview`
- **SCIM Status**: `GET /scim/status/{district_id}`

## Contributing

1. Follow PEP 8 style guidelines
2. Keep connector mappings in YAML/JSON files (no long Python literals)
3. Use async/await for I/O operations
4. Add comprehensive error handling
5. Update tests for new features

## License

Copyright (c) 2025 - Roster Sync Service
