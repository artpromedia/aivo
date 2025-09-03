# Stage-1 Docker Compose Setup

Complete Docker Compose configuration for running all Stage-1 services locally.

## Services Included

### Infrastructure
- **PostgreSQL 16** - Primary database (port 5432)
- **Redis 7** - Caching and session storage (port 6379)
- **MinIO** - S3-compatible object storage (ports 9000, 9001)
- **Redpanda** - Kafka-compatible event streaming (port 9092)
- **Kong Gateway** - API Gateway (ports 8000, 8001)
- **MailHog** - Email testing (ports 1025, 8025)

### S1 Core Services
- **auth-svc** - Authentication service (port 8081)
- **tenant-svc** - District/school management (port 8082)
- **payment-svc** - Seat purchasing (port 8083)
- **learner-svc** - Student management (port 8084)
- **enrollment-router-svc** - Enrollment routing (port 8085)
- **inference-gateway-svc** - AI/ML gateway (port 8086)
- **assessment-svc** - Assessment engine (port 8087)
- **approval-svc** - Approval workflows (port 8088)
- **iep-svc** - IEP management (port 8089)
- **notification-svc** - Email notifications (port 8090)
- **admin-portal-svc** - Admin dashboard API (port 8091)
- **private-fm-orchestrator** - Workflow orchestration (port 8092)

## Quick Start

### Start All Services
```bash
# From repository root
docker compose -f infra/compose/local.yml up -d
```

### Run Golden Path Verification
```bash
# Option 1: PowerShell (Windows)
./scripts/verify-stage1.ps1

# Option 2: Bash (Linux/Mac)
./scripts/verify-stage1.sh

# Option 3: Node.js directly
node scripts/verify-stage1.js
```

### Stop All Services
```bash
docker compose -f infra/compose/local.yml down
```

## Health Checks

All services include health checks that verify:
- Service startup completion
- Database connectivity
- External service dependencies

Health status can be monitored with:
```bash
docker compose -f infra/compose/local.yml ps
```

## Service URLs

Once running, services are accessible at:

| Service | URL | Description |
|---------|-----|-------------|
| Kong Gateway | http://localhost:8000 | Main API entry point |
| Kong Admin | http://localhost:8001 | Gateway administration |
| MailHog UI | http://localhost:8025 | Email testing interface |
| MinIO Console | http://localhost:9001 | Object storage admin |
| PostgreSQL | localhost:5432 | Database (user: postgres, pass: password) |
| Redis | localhost:6379 | Cache server |

## Development

### View Logs
```bash
# All services
docker compose -f infra/compose/local.yml logs -f

# Specific service
docker compose -f infra/compose/local.yml logs -f auth-svc
```

### Rebuild Service
```bash
# Rebuild and restart a service
docker compose -f infra/compose/local.yml up -d --build auth-svc
```

### Database Access
```bash
# Connect to PostgreSQL
docker exec -it monorepo_postgres psql -U postgres -d monorepo

# Connect to Redis
docker exec -it monorepo_redis redis-cli
```

## Verification Script

The `verify-stage1` script tests the complete golden path:

1. **Health Checks** - Verifies all services are responding
2. **District Setup** - Creates district, school, purchases seats  
3. **Enrollment** - Registers guardian, creates learner, enrolls
4. **Assessment** - Runs baseline assessment workflow
5. **IEP Process** - Drafts, submits, and approves IEP
6. **Admin Portal** - Verifies populated dashboard data

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check Docker daemon is running
docker info

# Check port conflicts
netstat -an | grep :8081
```

**Database connection errors:**
```bash
# Wait for PostgreSQL to be ready
docker compose -f infra/compose/local.yml logs postgres

# Check health status
docker compose -f infra/compose/local.yml ps postgres
```

**Build failures:**
```bash
# Clean rebuild all services
docker compose -f infra/compose/local.yml down
docker compose -f infra/compose/local.yml build --no-cache
docker compose -f infra/compose/local.yml up -d
```

### Reset Environment
```bash
# Stop and remove all containers, volumes, networks
docker compose -f infra/compose/local.yml down -v --remove-orphans

# Clean up Docker system
docker system prune -af
```

## Environment Variables

Key environment variables (all services have defaults for local development):

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string  
- `JWT_SECRET` - Authentication secret
- `OPENAI_API_KEY` - AI/ML API key (for inference-gateway)
- `SMTP_*` - Email configuration (uses MailHog by default)

## Network

All services run on the `monorepo_infra` bridge network, allowing:
- Service-to-service communication via container names
- External access via exposed ports
- Isolated environment from other Docker projects

## Volumes

Persistent data stored in Docker volumes:
- `postgres_data` - Database files
- `redis_data` - Cache persistence
- `minio_data` - Object storage files
- `redpanda_data` - Event stream data
