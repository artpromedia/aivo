# Device OTA & Heartbeat Service

S2A-10 — OTA & Heartbeat — Device firmware/app updates with rings and
rollback + heartbeat collection

## Overview

This service provides Over-The-Air (OTA) firmware and application updates
for IoT devices with staged deployment rings and automatic rollback
capabilities. It also collects device heartbeat telemetry for monitoring
and analytics.

## Features

### OTA Updates

- **Multi-stage Deployment**: Canary → Early → Broad → Production rings
- **Semver Support**: Semantic versioning with automatic rollback
- **File Management**: Secure firmware file storage with checksums
- **Rollback Capabilities**: Automatic and manual rollback on failure
- **Device Targeting**: Target specific device types and hardware models
- **Battery & Storage Checks**: Ensure devices meet minimum requirements

### Heartbeat Collection

- **Real-time Telemetry**: Device health, performance, and status monitoring
- **Location Tracking**: GPS coordinates with accuracy metrics
- **Error Reporting**: Crash logs and error tracking
- **Custom Metrics**: Extensible telemetry data collection
- **Network Monitoring**: Connection type and signal strength

## API Endpoints

### Firmware Updates

- `POST /api/v1/firmware` - Create new firmware update
- `GET /api/v1/firmware` - List firmware updates with filtering
- `GET /api/v1/firmware/{id}` - Get specific firmware update
- `PUT /api/v1/firmware/{id}` - Update firmware configuration
- `POST /api/v1/firmware/{id}/deploy` - Deploy to deployment ring

### Device Heartbeat

- `POST /api/v1/heartbeat` - Receive device heartbeat
- `GET /api/v1/heartbeat/{device_id}` - Get device heartbeat history
- `GET /api/v1/devices/status` - Get device status overview

### Health & Monitoring

- `GET /health/` - Service health check
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

## Deployment Rings

1. **Canary (5%)**: Initial testing with limited devices
2. **Early (25%)**: Early adopters and beta testers
3. **Broad (75%)**: General availability to most devices
4. **Production (100%)**: Full deployment to all devices

## Configuration

Environment variables (prefix: `DEVICE_OTA_`):

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/device_ota

# Storage
STORAGE_TYPE=local|s3
STORAGE_BASE_PATH=./storage/firmware
STORAGE_S3_BUCKET=firmware-bucket
STORAGE_S3_REGION=us-east-1

# Rollback
AUTO_ROLLBACK_FAILURE_THRESHOLD=10.0
ROLLBACK_TIMEOUT_HOURS=6

# Rate Limiting
RATE_LIMIT_HEARTBEAT=100/minute
RATE_LIMIT_UPDATE_CHECK=10/minute
```

## Database Schema

### Core Tables

- `firmware_updates`: Update metadata and configuration
- `device_updates`: Individual device update tracking
- `device_heartbeats`: Real-time device telemetry
- `deployment_rings`: Staged rollout configuration

### Key Features

- UUID primary keys for distributed systems
- Soft deletes with `is_deleted` flags
- JSON metadata fields for flexibility
- Foreign key relationships for data integrity
- Created/updated timestamps for audit trails

## Development

### Setup

```bash
# Install dependencies
poetry install

# Setup database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_firmware_service.py
```

## Production

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## Monitoring

The service includes comprehensive monitoring:

- Health check endpoints for Kubernetes probes
- Metrics collection for Prometheus
- Structured logging for observability
- Error tracking and alerting

## Security

- Digital signature verification for firmware files
- Rate limiting on all endpoints
- Input validation with Pydantic schemas
- SQL injection protection with SQLAlchemy ORM
