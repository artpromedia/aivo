# Content Moderation Service

A comprehensive Trust & Safety content moderation system for flagged content review and decision processing.

## Features

- **Moderation Queue**: Centralized queue for flagged content with filtering and prioritization
- **Decision Processing**: Approve, soft-block, hard-block, or escalate decisions with audit trail
- **Content Types**: Support for OCR uploads, chat messages, ink images, audio/video submissions
- **Severity Levels**: Low, medium, high, and critical severity classification
- **Audit Logging**: Comprehensive audit trail for all moderation actions
- **Statistics Dashboard**: Real-time statistics and performance metrics
- **Appeal System**: Built-in appeal workflow for contested decisions

## API Endpoints

### Queue Management

- `GET /moderation/queue` - Get moderation queue with filtering
- `GET /moderation/queue/{item_id}` - Get specific queue item
- `GET /moderation/stats` - Get queue statistics

### Decision Processing

- `POST /moderation/{item_id}/decision` - Make moderation decision
- `GET /moderation/audit` - Get audit logs

### Content Submission (for other services)

- `POST /moderation/submit` - Submit content for moderation

## Database Models

### ModerationQueueItem

- Content metadata and flagging information
- User and tenant context
- Status tracking and timestamps
- Confidence scores and severity levels

### ModerationDecision

- Decision details and reasoning
- Moderator information
- Expiration and appeal deadlines
- Escalation requirements

### AuditLog

- Complete audit trail
- Actor and action tracking
- Context and metadata storage
- Timestamp and IP logging

### ModerationAppeal

- Appeal submission and review
- Evidence and resolution tracking
- Status and timeline management

## Admin UI

The Admin UI provides a comprehensive interface for moderators:

### Queue Tab

- Filterable list of pending items
- Quick decision making
- Content preview and metadata
- Status and priority indicators

### Statistics Tab

- Queue overview metrics
- Breakdown by content type, severity, and status
- Top moderators leaderboard
- Performance analytics

### Audit Tab

- Searchable audit log
- Action history tracking
- Actor and timestamp information
- Context details

## Integration

### Learner Pipeline

The service integrates with the learner pipeline to:

- Hide blocked content from learners
- Apply soft-block warnings
- Remove hard-blocked content entirely
- Track content visibility status

### Other Services

Integration points for:

- Chat service (message flagging)
- Media service (image/video flagging)
- OCR service (text content flagging)
- Inference service (AI flagging)

## Deployment

### Docker

```bash
docker build -t moderation-svc .
docker run -p 8080:8080 moderation-svc
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `RATE_LIMIT_PER_MINUTE`: API rate limiting

### Health Check

The service provides health check at `/health` for monitoring and load balancer integration.

## Development

### Requirements

- Python 3.11+
- PostgreSQL 13+
- FastAPI
- SQLAlchemy
- Pydantic

### Setup

```bash
pip install -r requirements.txt
python main.py
```

### Testing

```bash
pytest tests/
```

## Trust & Safety Compliance

The moderation service is designed to support:

- **COPPA Compliance**: Child safety content filtering
- **FERPA Compliance**: Educational content privacy
- **Content Safety**: Harassment, violence, and hate speech detection
- **Academic Integrity**: Plagiarism and dishonesty prevention
- **Data Protection**: Personal information flagging and removal
