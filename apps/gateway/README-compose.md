# Gateway Services Docker Compose

This Docker Compose configuration sets up Kong API Gateway with PostgreSQL database.

## Services

### Kong API Gateway with PostgreSQL

- **kong-database**: PostgreSQL 16 Alpine database for Kong
- **kong**: Kong 3.7 Alpine API Gateway with database backend

## Prerequisites

1. Copy the environment template:

```bash
cp .env.example .env
```

1. Edit `.env` file and set your values:

```bash
KONG_PG_PASSWORD=your_secure_kong_password_here
```

## Usage

### Start all services:

```bash
docker compose up -d
```

### View logs:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f kong
```

### Health checks:

```bash
# Check Kong admin API
curl http://localhost:8001

# Check Kong proxy
curl http://localhost:8000
```

## Ports

| Service | Port | Description |
|---------|------|-------------|
| Kong Proxy | 8000 | API Gateway proxy port |
| Kong Admin | 8001 | Admin API port |

## Data Persistence

The following volume is created for data persistence:

- `kong-db-data`: PostgreSQL database data

## Configuration

### Kong Database Migration

Before first use, initialize the Kong database:

```bash
docker compose run --rm kong kong migrations bootstrap
```

## Troubleshooting

### Kong Issues

- Check database connection: `docker compose logs kong-database`
- Verify Kong configuration: `docker compose exec kong kong config`

### Resource Limits

Kong is configured with:

- Memory limit: 2GB
- Memory reservation: 512MB

Adjust these in the docker-compose.yml if needed for your environment.
