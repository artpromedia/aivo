# Device Policy Service

FastAPI-based microservice for managing device policies, kiosk mode, and
network allowlists in Mobile Device Management (MDM) systems.

## Features

### Core Policy Management

- **Kiosk Mode**: Single-app and multi-app kiosk configurations with app
  restrictions
- **Network Policies**: WiFi profile management, mobile data controls, and
  hotspot restrictions
- **DNS Filtering**: Category-based content blocking with custom rules and
  allowlists
- **Study Windows**: Time-based access controls with schedule enforcement
- **Network Allowlist**: Walled garden implementation for educational content
  filtering

### Technical Capabilities

- **Real-time Sync**: Long-poll synchronization for efficient device policy
  updates
- **Policy Versioning**: Checksums and version control with conflict detection
- **Bulk Operations**: Device fleet management and bulk policy assignments
- **Audit Logging**: Comprehensive tracking of policy changes and sync events
- **Health Monitoring**: Built-in health checks and metrics for observability

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Docker (optional)

### Installation

1. **Clone and Setup**

   ```bash
   cd services/device-policy-svc
   pip install -r requirements.txt
   ```

2. **Configure Environment**

   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/devicepolicy"
   export SECRET_KEY="your-secret-key"
   export LOG_LEVEL="INFO"
   ```

3. **Run Development Server**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Deployment

```bash
# Build image
docker build -t device-policy-svc .

# Run container
docker run -d \
  --name device-policy-svc \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/devicepolicy" \
  device-policy-svc
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI Schema**: <http://localhost:8000/openapi.json>

## Policy Types

### Kiosk Policy

Configure single-app or multi-app kiosk mode:

```json
{
  "policy_type": "kiosk",
  "config": {
    "mode": "single_app",
    "apps": [
      {
        "package_name": "com.aivo.study",
        "app_name": "Aivo Study",
        "auto_launch": true,
        "allow_exit": false,
        "fullscreen": true
      }
    ]
  }
}
```

### Network Policy

Manage WiFi, mobile data, and connectivity:

```json
{
  "policy_type": "network",
  "config": {
    "wifi_networks": [
      {
        "ssid": "SchoolWiFi",
        "security": "WPA2",
        "password": "school123",
        "auto_connect": true
      }
    ],
    "mobile_data": {"enabled": false},
    "hotspot": {"enabled": false}
  }
}
```

### DNS Policy

Content filtering and DNS controls:

```json
{
  "policy_type": "dns",
  "config": {
    "primary_dns": "1.1.1.1",
    "secondary_dns": "1.0.0.1",
    "blocked_categories": ["adult", "gambling", "social"],
    "custom_rules": [
      {"domain": "educational-site.com", "action": "allow"}
    ]
  }
}
```

### Study Window Policy

Time-based access restrictions:

```json
{
  "policy_type": "study_window", 
  "config": {
    "windows": [
      {
        "start_time": "09:00",
        "end_time": "15:00",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "timezone": "America/New_York"
      }
    ],
    "enforcement_mode": "strict"
  }
}
```

## Network Allowlist

The service provides a walled garden implementation for educational content:

### Add Allowlist Entries

```bash
POST /allowlist
{
  "entry_type": "domain",
  "value": "khan-academy.org",
  "category": "educational",
  "description": "Educational math content"
}
```

### Bulk Import

```bash
POST /allowlist/bulk
{
  "entries": [
    {"entry_type": "domain", "value": "coursera.org", "category": "educational"},
    {"entry_type": "url", "value": "https://edx.org/learn", "category": "educational"}
  ]
}
```

## Device Synchronization

### Long-Poll Sync

Devices can efficiently sync policies using long-polling:

```bash
GET /policy/sync?device_id=device123&timeout=30
```

Returns immediately if changes are available, or waits up to 30 seconds for updates.

### Assign Policies

```bash
POST /device-policies
{
  "device_id": "device123",
  "policy_id": "policy-uuid"
}
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/test_services.py -v

# Integration tests  
pytest tests/test_api.py -v

# All tests
pytest -v
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy app/
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new policy type"

# Apply migrations
alembic upgrade head
```

## Monitoring

### Health Check

```bash
GET /health
```

### Metrics

- Policy assignment counts
- Sync request rates  
- Active device counts
- Policy version distributions

## Security

- **Authentication**: JWT token validation
- **Authorization**: Role-based access control
- **Input Validation**: Pydantic schema validation
- **SQL Injection**: SQLAlchemy ORM protection
- **Container Security**: Non-root user, minimal base image

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `SECRET_KEY` | - | JWT signing secret |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `["*"]` | CORS allowed origins |
| `API_PREFIX` | `/api/v1` | API path prefix |

## Architecture

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Device Apps   │    │   Admin Portal   │    │   MDM Console   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                        │
         │ Long-poll sync        │ Policy management     │ Bulk operations
         ▼                       ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                         │
├─────────────────────────────────────────────────────────────────┤
│  Policy Service  │  Sync Service  │  Allowlist Service         │
├─────────────────────────────────────────────────────────────────┤
│                     SQLAlchemy ORM                             │
├─────────────────────────────────────────────────────────────────┤
│                    PostgreSQL Database                         │
└─────────────────────────────────────────────────────────────────┘
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
