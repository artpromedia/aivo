# Media Service

Media Service for video uploads, HLS transcoding, and Zoom LTI integration supporting educational live sessions with comprehensive attendance tracking.

## Features

###  Video Processing
- **Presigned S3 Uploads**: Direct browser-to-S3 uploads for large video files
- **HLS Transcoding**: Automatic conversion to adaptive bitrate streaming using FFmpeg
- **Multi-quality Output**: 360p, 480p, 720p, 1080p variants with adaptive streaming
- **Progress Tracking**: Real-time transcoding progress updates

###  Access Control
- **Token-based Authentication**: Secure access tokens for HLS content
- **Playlist Proxy**: Whitelist-based proxy for HLS playlists and segments  
- **User Validation**: Organization and course-level access control
- **CDN Integration**: CloudFront/CDN support for global content delivery

###  LTI Integration
- **LTI 1.3 Compliance**: Full support for Learning Tools Interoperability 1.3
- **Zoom Integration**: Seamless Zoom meeting creation and management
- **JWT Verification**: Secure LTI launch request validation
- **Multi-tenant**: Support for multiple organizations and courses

###  Attendance Tracking
- **Real-time Updates**: Live attendance tracking via Zoom webhooks
- **Detailed Reports**: Comprehensive attendance analytics and reporting
- **Participant Management**: Join/leave tracking with duration calculations
- **Export Capabilities**: CSV and JSON export for attendance data

## Architecture

```
        
   Frontend             Media API            Background    
   Application      (FastAPI)        Workers       
                                             (Celery)      
        
                                                       
                                                       
                           
                          PostgreSQL           FFmpeg        
                          Database             Transcoder    
                           
                                                       
                                                       
                           
                          Redis Cache          S3 Storage    
                          & Queue              & CDN         
                           
```

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- FFmpeg 4.4+
- Poetry for dependency management

### Installation

1. **Clone and setup**:
```bash
cd services/media-svc
poetry install
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Database setup**:
```bash
# Run migrations
alembic upgrade head
```

4. **Start services**:
```bash
# API server
poetry run uvicorn app.main:app --reload

# Celery worker (separate terminal)
poetry run celery -A app.workers.celery_app worker --loglevel=info

# Celery beat scheduler (separate terminal)  
poetry run celery -A app.workers.celery_app beat --loglevel=info
```

### Development

Run code quality checks:
```bash
make py-fix  # Runs ruff fix + format
make test    # Run test suite
make lint    # Run linting only
```

## API Documentation

### Video Upload Flow

1. **Request presigned upload URL**:
```bash
POST /api/v1/media/presigned-upload
{
  "filename": "lecture-01.mp4",
  "content_type": "video/mp4", 
  "file_size": 104857600
}
```

2. **Upload directly to S3** using the presigned URL

3. **Complete upload and start transcoding**:
```bash
POST /api/v1/media/uploads/{upload_id}/complete
```

4. **Monitor transcoding progress** via upload status

### HLS Playback Flow

1. **Generate access token**:
```bash
GET /api/v1/media/hls/{video_id}/access-token?user_id={user_id}
```

2. **Access master playlist**:
```bash
GET /api/v1/media/hls/{video_id}/master.m3u8?token={access_token}
```

3. **Player automatically requests variant playlists and segments**

### Live Session Flow

1. **Create LTI configuration**:
```bash
POST /api/v1/lti/config
{
  "organization_id": "...",
  "client_id": "...",
  "issuer": "...", 
  "deployment_id": "...",
  "zoom_api_key": "...",
  "zoom_api_secret": "..."
}
```

2. **Handle LTI launch**:
```bash  
POST /api/v1/lti/launch
{
  "id_token": "...",
  "organization_id": "..."
}
```

3. **Create live session**:
```bash
POST /api/v1/live-sessions  
{
  "session_name": "Weekly Lecture",
  "scheduled_start": "2024-01-15T10:00:00Z",
  "scheduled_end": "2024-01-15T11:30:00Z", 
  "zoom_host_id": "zoom-user-id",
  "lti_config_id": "..."
}
```

4. **Monitor attendance**:
```bash
GET /api/v1/live-sessions/{session_id}/attendance
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/media_db

# Redis  
REDIS_URL=redis://localhost:6379/0

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET=your-media-bucket
S3_CDN_URL=https://your-cloudfront-domain.com

# Security
HLS_PROXY_SECRET=your-secret-key-for-hls-tokens
JWT_SECRET_KEY=your-jwt-secret

# Zoom
ZOOM_WEBHOOK_SECRET=your-zoom-webhook-secret

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### FFmpeg Configuration

Default transcoding settings create multiple quality variants:

- **360p**: 800kbps bitrate, 640x360 resolution
- **480p**: 1400kbps bitrate, 854x480 resolution  
- **720p**: 2800kbps bitrate, 1280x720 resolution
- **1080p**: 5000kbps bitrate, 1920x1080 resolution

Customize in `app/workers/transcode.py`.

## Deployment

### Docker

```bash
# Build image
docker build -t media-service .

# Run container
docker run -d \
  --name media-service \
  -p 8000:8000 \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  media-service
```

### Docker Compose

```yaml
version: '3.8'
services:
  media-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/media
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  media-worker:
    build: .
    command: celery -A app.workers.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/media
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db  
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=media
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    
volumes:
  postgres_data:
```

## Security Considerations

### Access Control
- All HLS content requires valid access tokens
- Tokens include user ID and video ID validation
- Configurable token expiration (default: 1 hour)

### LTI Security  
- Full JWT signature verification using platform public keys
- Nonce validation to prevent replay attacks
- Deployment ID validation for multi-tenant security

### Webhook Security
- HMAC signature validation for Zoom webhooks
- Request timestamp validation to prevent replay attacks

## Monitoring & Observability

### Health Checks
- `/health` endpoint for load balancer health checks
- Database connectivity validation
- Redis connectivity validation  

### Logging
- Structured JSON logging for production
- Request/response logging with correlation IDs
- Performance metrics for transcoding operations

### Metrics
- Prometheus metrics endpoint: `/metrics`
- Custom metrics for video processing pipeline
- Attendance tracking analytics

## Contributing

1. **Code Style**: Follow PEP 8, use black formatter
2. **Type Hints**: Required for all function signatures  
3. **Testing**: Minimum 80% test coverage required
4. **Documentation**: Update docstrings and README for changes

### Pre-commit Hooks

```bash
# Install pre-commit
poetry run pre-commit install

# Run checks manually
poetry run pre-commit run --all-files
```

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: [Internal Wiki](https://wiki.example.com/media-service)
- **Issues**: [JIRA Project](https://example.atlassian.net/projects/MEDIA)
- **Slack**: #media-service-support
