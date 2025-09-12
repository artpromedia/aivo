# SSO Service

Enterprise Single Sign-On (SSO) and SAML Identity Provider service for AIVO platform.

## Features

- **SAML 2.0 Authentication**: Full SAML SSO support with metadata exchange
- **Identity Provider Integration**: Okta, Azure AD, Google Workspace support
- **Just-In-Time (JIT) Provisioning**: Automatic user creation on first login
- **Role Mapping**: Group-to-role and attribute-to-field mappings
- **Multi-Tenant**: Tenant-specific SSO configurations
- **Security**: Encrypted assertions, signature validation, replay protection

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Poetry for dependency management

### Installation

1. **Clone and setup:**

   ```bash
   cd services/sso-svc
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

   # Run database migrations
   poetry run alembic upgrade head

   # Start API server
   poetry run python -m app.main
   ```

4. **Access API documentation:**

   - Swagger UI: <http://localhost:8200/docs>
   - ReDoc: <http://localhost:8200/redoc>

## API Endpoints

### SAML Authentication

- `GET /saml/metadata` - SAML service provider metadata
- `POST /saml/acs` - Assertion Consumer Service (callback)
- `GET /saml/sls` - Single Logout Service
- `GET /saml/login/{provider_id}` - Initiate SAML login

### Identity Provider Management

- `POST /providers` - Create identity provider configuration
- `GET /providers` - List identity providers
- `PUT /providers/{id}` - Update provider configuration
- `DELETE /providers/{id}` - Delete provider

### Role Mappings

- `GET /mappings` - Get role mappings for tenant
- `POST /mappings` - Create role mapping
- `PUT /mappings/{id}` - Update role mapping
- `DELETE /mappings/{id}` - Delete role mapping

### Health & Monitoring

- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics
- `GET /` - Service information

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sso_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-secret-key
SAML_PRIVATE_KEY_PATH=/path/to/saml.key
SAML_CERTIFICATE_PATH=/path/to/saml.crt

# Service
SERVICE_PORT=8200
LOG_LEVEL=INFO
ENVIRONMENT=development

# External Services
AUTH_SVC_URL=http://auth-svc:8000
TENANT_SVC_URL=http://tenant-svc:8100
```

### SAML Configuration

The service supports standard SAML 2.0 configurations:

- **Entity ID**: Unique identifier for the service provider
- **ACS URL**: Assertion Consumer Service endpoint
- **SLS URL**: Single Logout Service endpoint
- **Certificate**: X.509 certificate for signature validation
- **Attribute Mappings**: Map SAML attributes to user fields

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_saml.py
```

### Code Quality

```bash
# Format code
poetry run black app tests

# Lint code
poetry run ruff check app tests

# Type checking
poetry run mypy app
```

## Architecture

```text
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Identity      │────│  SSO Service │────│ Auth Service│
│   Provider      │    │              │    │             │
│ (Okta/Azure/G)  │    │   SAML 2.0   │    │    Users    │
└─────────────────┘    └──────────────┘    └─────────────┘
                              │
                       ┌──────────────┐
                       │    Redis     │
                       │   (Cache)    │
                       └──────────────┘
```

## Security Considerations

- All SAML assertions are validated for signatures and timestamps
- Replay protection prevents assertion reuse
- JIT provisioning follows principle of least privilege
- Role mappings are validated against tenant permissions
- All communications use TLS encryption

## Monitoring

The service exposes Prometheus metrics for:

- SAML authentication attempts (success/failure)
- JIT provisioning statistics
- Role mapping usage
- Response times and error rates

## License

Copyright (c) 2025 AIVO. All rights reserved.
