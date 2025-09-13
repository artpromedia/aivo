# Audit Log Service

Immutable audit logging service with WORM (Write Once, Read Many) compliance and hash chain verification.

## Features

- **WORM Compliance**: Audit events are immutable after creation
- **Hash Chain Verification**: SHA-256 based tamper detection
- **Searchable API**: Filter and search audit events with pagination
- **Export Functionality**: Export to CSV, JSON, or Excel with S3 storage
- **Real-time Statistics**: Monitor audit activity and integrity
- **Thread-Safe Operations**: Concurrent event creation with hash chain consistency

## API Endpoints

### Health Checks

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check with database verification
- `GET /health/live` - Liveness check for Kubernetes

### Audit Events

- `POST /api/v1/audit` - Create new audit event
- `GET /api/v1/audit` - Search and list audit events
- `GET /api/v1/audit/{id}` - Get specific audit event
- `POST /api/v1/audit/verify` - Verify hash chain integrity
- `GET /api/v1/audit/stats` - Get audit statistics

### Export Jobs

- `POST /api/v1/export` - Create export job
- `GET /api/v1/export` - List export jobs
- `GET /api/v1/export/{id}` - Get export job details
- `GET /api/v1/export/{id}/download` - Get download URL
- `GET /api/v1/export/formats` - Available export formats

## Environment Configuration

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/audit_db

# Environment
ENVIRONMENT=development  # development, staging, production

# AWS S3 (for exports)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-west-2
S3_BUCKET_NAME=your-audit-exports-bucket

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379

# Security
CORS_ORIGINS=["http://localhost:3000"]
```

## Database Setup

The service requires PostgreSQL with WORM compliance triggers:

```sql
-- Create database
CREATE DATABASE audit_db;

-- Connect to database and run migrations
-- (Handled automatically by the application)
```

## Running the Service

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/audit_db"

# Run the service
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build image
docker build -t audit-log-service .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:password@host.docker.internal/audit_db" \
  audit-log-service
```

### Docker Compose

```yaml
version: '3.8'
services:
  audit-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/audit_db
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=audit_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Usage Examples

### Creating an Audit Event

```bash
curl -X POST "http://localhost:8000/api/v1/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user.login",
    "user_id": "user123",
    "action": "successful_login",
    "resource_type": "authentication",
    "resource_id": "session_456",
    "details": {
      "login_method": "password",
      "device_type": "web"
    },
    "risk_level": "low",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  }'
```

### Searching Audit Events

```bash
curl "http://localhost:8000/api/v1/audit?event_type=user.login&start_date=2024-01-01T00:00:00&page=1&page_size=50"
```

### Creating an Export Job

```bash
curl -X POST "http://localhost:8000/api/v1/export?requested_by=admin" \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "Monthly Audit Report",
    "export_format": "xlsx",
    "filters": {
      "start_date": "2024-01-01T00:00:00",
      "end_date": "2024-01-31T23:59:59"
    }
  }'
```

### Verifying Hash Chain

```bash
curl -X POST "http://localhost:8000/api/v1/audit/verify" \
  -H "Content-Type: application/json" \
  -d '{"verify_all": true}'
```

## WORM Compliance

The service implements WORM compliance through:

1. **Database Triggers**: PostgreSQL triggers prevent UPDATE and DELETE operations on audit events
2. **Hash Chains**: Each event includes a hash of the previous event, creating an immutable chain
3. **Tamper Detection**: Hash chain verification can detect any modifications to the audit log

## Security Features

- **Immutable Records**: Once created, audit events cannot be modified or deleted
- **Hash Chain Integrity**: Sequential hash linking prevents tampering
- **Structured Logging**: All service operations are logged for monitoring
- **Input Validation**: Comprehensive request validation using Pydantic
- **Error Handling**: Secure error responses without information disclosure

## Monitoring

### Health Endpoints

- Basic health: `GET /health`
- Database connectivity: `GET /health/ready`
- Application status: `GET /health/live`

### Metrics

- Total audit events
- Events in last 24 hours
- Unique users in last 24 hours
- High-risk events count
- Hash chain verification status

## Testing & Development

### Running Tests

```bash
pytest tests/ -v --cov=app
```

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/
```

## License

This project is part of the AIVO audit system and follows the project's licensing terms.
