# Approval Service

Dual participant approval workflows with TTL (Time To Live) and webhook notifications.

## Features

- **Dual Participant Approvals**: Requires approval from both guardian and teacher/administrator
- **Time-to-Live (TTL)**: Automatic expiration of approval requests
- **Webhook Notifications**: Real-time notifications for approval events
- **Multi-tenant Support**: Isolated approvals per tenant
- **Background Tasks**: Automated reminders and cleanup
- **Comprehensive API**: REST endpoints for all approval operations

## Architecture

- **FastAPI**: Modern async web framework
- **SQLAlchemy**: Async ORM with PostgreSQL
- **Celery**: Background task processing
- **Redis**: Caching and task queue
- **Pydantic**: Data validation and serialization

## API Endpoints

### Core Endpoints

- `POST /approvals` - Create new approval request
- `GET /approvals` - List approvals with filtering
- `GET /approvals/{id}` - Get approval by ID
- `POST /approvals/{id}/decision` - Make approval decision
- `GET /approvals/{id}/status` - Get approval status

### Utility Endpoints

- `GET /health` - Health check
- `GET /` - Service information

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Using poetry
poetry install
```

### 2. Environment Configuration

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/approval_db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Webhook settings
WEBHOOK_TIMEOUT=30.0
WEBHOOK_RETRY_ATTEMPTS=3

# TTL settings
DEFAULT_TTL_HOURS=72
MAX_TTL_HOURS=720
```

### 3. Start the Service

```bash
# Development
python run.py --reload --debug

# Production
python run.py --host 0.0.0.0 --port 8080 --workers 4
```

### 4. Start Background Tasks

```bash
# Start Celery worker
celery -A app.tasks worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.tasks beat --loglevel=info
```

## Usage Examples

### Create Approval Request

```python
import httpx

approval_data = {
    "tenant_id": "school_district_1",
    "approval_type": "iep_document",
    "priority": "normal",
    "resource_type": "iep_document",
    "resource_id": "iep_12345",
    "title": "IEP Approval for John Doe",
    "description": "Annual IEP review requires dual approval",
    "created_by": "teacher_smith",
    "ttl_hours": 72,
    "participants": [
        {
            "user_id": "parent_jane_doe",
            "email": "jane.doe@email.com",
            "role": "guardian",
            "display_name": "Jane Doe",
            "is_required": True
        },
        {
            "user_id": "teacher_smith",
            "email": "smith@school.edu",
            "role": "teacher",
            "display_name": "Ms. Smith",
            "is_required": True
        }
    ],
    "webhook_url": "https://your-app.com/webhooks/approval",
    "webhook_events": ["approval_requested", "approval_completed"]
}

response = httpx.post("http://localhost:8080/approvals", json=approval_data)
approval = response.json()
```

### Make Decision

```python
decision_data = {
    "decision_type": "approve",
    "comments": "IEP goals look appropriate for the student's needs"
}

response = httpx.post(
    f"http://localhost:8080/approvals/{approval_id}/decision",
    json=decision_data,
    params={"user_id": "parent_jane_doe"}
)
```

### List Approvals

```python
response = httpx.get(
    "http://localhost:8080/approvals",
    params={
        "tenant_id": "school_district_1",
        "status": "pending",
        "limit": 20
    }
)
approvals = response.json()
```

## Webhook Events

The service sends webhooks for the following events:

- `approval_requested` - New approval created
- `decision_made` - Participant made a decision
- `approval_completed` - All required approvals received
- `approval_rejected` - Approval was rejected
- `approval_expired` - Approval expired due to TTL
- `reminder_sent` - Reminder notification sent

### Webhook Payload Example

```json
{
    "event_type": "approval_completed",
    "timestamp": "2025-09-02T10:30:00Z",
    "approval_id": "123e4567-e89b-12d3-a456-426614174000",
    "tenant_id": "school_district_1",
    "data": {
        "approval_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "approved",
        "title": "IEP Approval for John Doe",
        "approval_progress": {
            "total_participants": 2,
            "approved_count": 2,
            "rejected_count": 0,
            "pending_count": 0,
            "completion_percentage": 100
        }
    },
    "callback_data": {
        "source": "iep_service",
        "reference_id": "iep_12345"
    }
}
```

## Approval Workflow

1. **Creation**: Approval request created with dual participants (guardian + staff)
2. **Notification**: Participants receive email/SMS notifications
3. **Decision Making**: Each participant approves or rejects
4. **Completion**:
   - **Approved**: All required approvals received
   - **Rejected**: Any participant rejects
   - **Expired**: TTL reached without completion
5. **Webhooks**: Events sent to configured endpoints
6. **Cleanup**: Background tasks handle reminders and expiration

## Participant Roles

- `guardian` - Parent or legal guardian
- `teacher` - Classroom teacher
- `administrator` - School administrator
- `special_education_coordinator` - Special education coordinator
- `principal` - School principal

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_approval_service.py

# Run with verbose output
pytest -v
```

## Configuration

Key configuration options in `app/config.py`:

- **TTL Settings**: Default and max TTL hours
- **Reminder Schedule**: When to send reminder notifications
- **Webhook Settings**: Timeout and retry configuration
- **Database**: Connection pooling and settings
- **Multi-tenancy**: Enable/disable tenant isolation

## Background Tasks

The service includes several background tasks:

- **Expiration Task**: Automatically expires overdue approvals
- **Reminder Task**: Sends reminder notifications before expiry
- **Notification Task**: Handles email/SMS notifications
- **Cleanup Task**: Maintains database performance

## Security

- **Tenant Isolation**: Strict separation of tenant data
- **Participant Validation**: Only assigned participants can make decisions
- **Request Metadata**: Tracks IP addresses and user agents
- **Input Validation**: Comprehensive validation using Pydantic

## Monitoring

- **Health Checks**: `/health` endpoint for service status
- **Logging**: Structured logging with configurable levels
- **Metrics**: Background task execution metrics
- **Database**: Connection pool monitoring

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY run.py .

EXPOSE 8080
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8080"]
```

### Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/approval_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
DEBUG=false
LOG_LEVEL=INFO
```

## License

MIT License - see LICENSE file for details.
