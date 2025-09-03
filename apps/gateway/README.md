# Kong Gateway Configuration for S1 Services

This Kong Gateway configuration provides API routing, JWT authentication,
RBAC (Role-Based Access Control), and rate limiting for all S1 microservices.

## Services Configured

### 🔐 Authentication Services

- **auth-service** (port 8080): `/auth/login`, `/auth/refresh`
  - Public endpoints with rate limiting
  - Login: 10/min, 100/hour, 1000/day

### 🏢 Administrative Services (Staff/District Admin Only)

- **tenant-service** (port 8081): `/tenant/*`
- **payment-service** (port 8082): `/payment/*`
- **admin-portal-service** (port 8095): `/admin/*`

### 👥 Staff Services (Staff/District Admin Only)

- **approval-service** (port 8083): `/approval/*`
- **notification-service** (port 8084): `/notification/*`, `/notify/*`

### 🤖 AI Services (Authenticated Users)

- **inference-gateway-service** (port 8096): `/inference/*`
  - Rate limited: 60/min, 1000/hour, 10000/day
  - JWT authentication required

## Authentication & Authorization

### JWT Configuration

- **Header**: `Authorization: Bearer <token>`
- **Query Param**: `?token=<token>`
- **Algorithm**: HS256
- **Claims Verified**: `exp`, `role` (admin routes), `exp` only (inference)

### Role-Based Access Control (RBAC)

- **staff**: Access to approval and notification services
- **district_admin**: Access to all admin and staff services
- **system_admin**: Full access (via consumer configuration)

### Consumers

- `system-admin`: Full system access
- `district-admin`: District-level administrative access
- `staff-user`: Staff-level service access

## Rate Limiting

### Authentication Endpoints

- **Login**: 10 requests/minute, 100/hour, 1000/day
- **Refresh**: No rate limiting (relies on JWT expiration)

### Inference Endpoints

- **Inference**: 60 requests/minute, 1000/hour, 10000/day

## Global Features

### CORS Support

- Origins: `*` (configure for production)
- Methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
- Headers: Standard + `Authorization`, `X-Auth-Token`

### Observability

- **Prometheus Metrics**: Per-consumer, status codes, latency, bandwidth
- **Access Logs**: Stdout for proxy and admin
- **Error Logs**: Stderr for proxy and admin

## Service Ports

| Service | Internal Port | Kong Route |
|---------|---------------|------------|
| Auth Service | 8080 | `/auth/*` |
| Tenant Service | 8081 | `/tenant/*` |
| Payment Service | 8082 | `/payment/*` |
| Approval Service | 8083 | `/approval/*` |
| Notification Service | 8084 | `/notification/*`, `/notify/*` |
| Admin Portal Service | 8095 | `/admin/*` |
| Inference Gateway | 8096 | `/inference/*` |

## Kong Gateway Ports

- **Proxy**: 8000 (API Gateway)
- **Admin**: 8001 (Kong Admin API)

## Deployment

### Using Docker Compose

```bash
# Start Kong Gateway
cd apps/gateway
docker compose up -d

# Verify configuration
curl http://localhost:8001/status
```

### Configuration Validation

```bash
# Validate YAML syntax
yamllint kong.yml

# Validate Docker Compose
docker compose config
```

## Security Notes

⚠️ **Production Considerations**:

1. Replace JWT secrets with secure, environment-specific values
2. Configure CORS origins for specific domains
3. Set up proper SSL/TLS termination
4. Implement proper secret management
5. Configure rate limiting based on actual usage patterns
6. Set up monitoring and alerting for rate limit violations

## API Access Examples

### Public Authentication

```bash
# Login (rate limited)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

### Authenticated Admin Access

```bash
# Admin dashboard (requires staff/district_admin role)
curl -X GET http://localhost:8000/admin/summary?tenant_id=123 \
  -H "Authorization: Bearer <jwt_token>"
```

### Inference API Access

```bash
# AI inference (rate limited, requires valid JWT)
curl -X POST http://localhost:8000/inference/predict \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world"}'
```

This configuration uses Kong's declarative format version 3.0 with transform
enabled.

### Structure

- **Services**: Backend services that Kong will proxy to
- **Routes**: Request routing rules to match incoming requests to services
- **Plugins**: Kong plugins for authentication, rate limiting, etc.
- **Upstreams**: Load balancing configuration for multiple service instances
- **Consumers**: API consumers for authentication and rate limiting

## Usage

The configuration file can be used with Kong in declarative mode:

```bash
kong start -c kong.conf --declarative-config kong.yml
```

## Validation

Validate the configuration using yamllint:

```bash
yamllint apps/gateway/kong.yml
```
