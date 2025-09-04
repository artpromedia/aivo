# Lesson Registry Service

A FastAPI-based service for managing versioned lessons with signed CDN assets and
search functionality.

## Features

- **Versioned Lessons**: Create and manage multiple versions of lessons with
  DRAFT/PUBLISHED states
- **Role-based Access Control**: Teachers can create drafts, admins/district
  admins can publish
- **Signed CDN Assets**: Presigned URLs for secure asset delivery
  (MinIO/CloudFront) with 600s expiry
- **Search & Discovery**: Search by subject, grade band, keywords with
  pagination
- **Asset Management**: Support for multiple asset types (video, document,
  image, audio, interactive)
- **RESTful API**: Comprehensive REST API with OpenAPI documentation

## Architecture

### Database Schema

#### Tables
- `lessons`: Core lesson metadata
- `lesson_versions`: Versioned lesson content 
- `lesson_assets`: Asset metadata with CDN references

#### States
- `DRAFT`: Editable by teachers, not visible to learners
- `PUBLISHED`: Read-only, visible to learners

### RBAC (Role-Based Access Control)
- **Teachers**: Can create/edit their own lesson drafts
- **Admins/District Admins**: Can publish any lesson in their tenant

### CDN Integration
- **MinIO/S3**: Asset storage backend
- **CloudFront**: Optional CDN for global distribution
- **Presigned URLs**: Secure, time-limited asset access (expires=600s)

## Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- PostgreSQL
- MinIO or AWS S3

### Installation

1. Clone and navigate to the service:
```bash
cd services/lesson-registry-svc
```

1. Install dependencies:

```bash
poetry install
```

1. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

1. Run database migrations:

```bash
poetry run alembic upgrade head
```

1. Start the service:

```bash
poetry run python run.py
```

The service will be available at http://localhost:8003

### Docker

Build and run with Docker:
```bash
docker build -t lesson-registry-svc .
docker run -p 8003:8003 lesson-registry-svc
```

## Configuration

Key environment variables:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lesson_registry

# AWS/MinIO
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET=lesson-assets
S3_ENDPOINT_URL=http://localhost:9000  # For MinIO
CLOUDFRONT_DOMAIN=your-cloudfront-domain.com
ASSET_URL_EXPIRY=600

# Auth
JWT_SECRET_KEY=your-secret-key-change-in-production
```

## API Usage

### Authentication
All endpoints require JWT bearer token:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8003/api/v1/lessons
```

### Create a Lesson
```bash
curl -X POST http://localhost:8003/api/v1/lessons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "Introduction to Python",
    "description": "Learn Python basics",
    "subject": "Computer Science", 
    "grade_band": "9-12",
    "keywords": ["python", "programming"]
  }'
```

### Create a Version
```bash
curl -X POST http://localhost:8003/api/v1/lessons/{lesson_id}/versions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "content": {
      "slides": [
        {"title": "Welcome", "content": "Introduction to the course"}
      ]
    },
    "summary": "Course introduction",
    "learning_objectives": ["Understand Python basics"],
    "duration_minutes": 45
  }'
```

### Publish a Version (Admin only)
```bash
curl -X POST http://localhost:8003/api/v1/versions/{version_id}/publish \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Add an Asset
```bash
curl -X POST http://localhost:8003/api/v1/versions/{version_id}/assets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "intro-video.mp4",
    "asset_type": "video",
    "file_path": "/videos/intro-video.mp4",
    "file_size": 5242880,
    "mime_type": "video/mp4"
  }'
```

### Search Lessons
```bash
curl "http://localhost:8003/api/v1/search?q=python&subject=Computer%20Science&grade_band=9-12" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Development

### Running Tests
```bash
poetry run pytest
```

### Code Quality
```bash
# Format code
poetry run black .

# Lint code  
poetry run flake8 .

# Type checking
poetry run mypy .
```

### Database Migrations

Create a new migration:
```bash
poetry run alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
poetry run alembic upgrade head
```

## API Documentation

- **OpenAPI Spec**: `/docs/api/rest/lesson-registry.yaml`
- **Interactive Docs**: http://localhost:8003/docs (when running)
- **ReDoc**: http://localhost:8003/redoc (when running)

## Health Monitoring

- **Health Check**: `GET /healthz`
- **Metrics**: `GET /metrics`
- **Service Info**: `GET /`

## Security

- **JWT Authentication**: All endpoints require valid JWT tokens
- **RBAC**: Role-based permissions for different operations
- **Signed URLs**: Time-limited, secure asset access
- **Input Validation**: Comprehensive request validation with Pydantic
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

## Performance

- **Async/Await**: Full async support with FastAPI and SQLAlchemy
- **Connection Pooling**: Database connection pooling
- **CDN Integration**: Offload asset delivery to CDN
- **Pagination**: Efficient search with pagination
- **Indexes**: Database indexes on commonly queried fields

## Monitoring & Observability

- **Structured Logging**: JSON logs with correlation IDs
- **Health Checks**: Database and storage connectivity checks
- **Metrics**: Basic service metrics (can be extended)
- **Error Handling**: Comprehensive error responses

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass
5. Submit pull request

## License

Copyright (c) 2025 Aivo. All rights reserved.
