# Device Enrollment & Attestation Service

Aivo Pad device enrollment and certificate attestation service.

## Overview

This service handles:

- Device enrollment with serial number and hardware fingerprint verification
- Attestation challenge generation and verification
- Device certificate issuance and management
- Device lifecycle management (revocation, expiration)

## API Endpoints

### Device Enrollment

- `POST /api/v1/enroll` - Enroll new device
- Returns device ID and bootstrap token

### Device Attestation  

- `POST /api/v1/attest/challenge` - Request attestation challenge
- `POST /api/v1/attest` - Submit signed challenge for certificate

### Device Management

- `GET /api/v1/devices/{id}` - Get device information
- `GET /api/v1/devices` - List devices (paginated)
- `POST /api/v1/devices/{id}/revoke` - Revoke device certificate

### System

- `GET /api/v1/health` - Health check
- `GET /` - Service information

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations (if using Alembic)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Database Schema

- `devices` - Device enrollment records
- `attestation_challenges` - Challenge/response tracking
- `device_audit_logs` - Audit trail for device operations

### Environment Variables

See `.env.example` for configuration options.

## Production Deployment

### Docker

```bash
# Build image
docker build -t device-enroll-svc .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  device-enroll-svc
```

### Security Considerations

- Use strong secret keys in production
- Configure proper CORS origins
- Enable TLS/SSL termination
- Secure database connections
- Implement proper key management for CA operations

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```
