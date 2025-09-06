# Search Service

Unified search service with OpenSearch, RBAC filtering, and PII masking capabilities.

## Features

- **OpenSearch Integration**: Full-text search across lessons, coursework, and
  learner profiles
- **RBAC Filtering**: Role-based access control for guardians, teachers,
  district admins
- **PII Masking**: Automatic masking of personally identifiable information
  based on user permissions
- **Caching**: Redis-based response caching for improved performance
- **Multi-Index Search**: Search across multiple content types with scoped
  queries

## API Endpoints

### Search

```http
GET /search?q=<query>&scope=<lessons|coursework|learners|all>
```

### Suggestions

```http
GET /suggest?q=<query>&scope=<lessons|coursework|learners|all>
```

### Health Check

```http
GET /health
```

### Document Management

```http
POST /index          # Index single document
POST /bulk-index     # Bulk index documents
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG` | Debug mode | `false` |
| `OPENSEARCH_HOST` | OpenSearch host | `localhost` |
| `OPENSEARCH_PORT` | OpenSearch port | `9200` |
| `OPENSEARCH_USERNAME` | OpenSearch username | `admin` |
| `OPENSEARCH_PASSWORD` | OpenSearch password | `admin` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_ENABLED` | Enable Redis caching | `true` |
| `PII_MASKING_ENABLED` | Enable PII masking | `true` |

## RBAC Rules

### System Admin

- Full access to all content
- Can see unmasked PII data
- Can index/manage documents

### District Admin

- Access to all content in their district
- Can see unmasked PII for district users
- Can index/manage documents

### Teacher

- Access to their classes and students
- Can see unmasked PII for their students
- Read-only access

### Guardian

- Access to their learners' content only
- Can see unmasked PII for their learners
- Read-only access

### Learner

- Access to public lessons and their own profile
- Cannot see other learners' data
- Read-only access

## PII Masking

The service automatically masks sensitive data:

- SSNs → "***-**-****" (pattern replaced)
- Email → "***@***.com" (partial masking)
- Phone → "(***) ***-****" (format preserved)
- Names → "Learner ABC123" (consistent hash-based)

Non-authorized users see masked data while authorized roles
(based on RBAC) see unmasked content.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload

# Run tests
pytest tests/

# Check types
mypy app/
```

## Docker

```bash
# Build image
docker build -t search-service .

# Run container
docker run -p 8000:8000 \
  -e OPENSEARCH_HOST=opensearch \
  -e REDIS_HOST=redis \
  search-service
```

## Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│  Search Service │────│ OpenSearch      │
│   (REST API)    │    │  (Orchestrator) │    │ (Full-text)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │  RBAC Service   │    │ PII Masking     │
         │              │  (Access Ctrl)  │    │ (Data Privacy)  │
         │              └─────────────────┘    └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         └──────────────│ Redis Cache     │
                        │ (Performance)   │
                        └─────────────────┘
```
