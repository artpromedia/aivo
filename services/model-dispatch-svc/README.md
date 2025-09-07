# Model Dispatch Policy Service

LLM provider routing service with data residency enforcement and intelligent
dispatch policies.

## Overview

The Model Dispatch Policy Service determines the appropriate LLM provider for
requests based on:

- Subject matter expertise
- Grade band requirements
- Regional data residency policies
- Teacher overrides and preferences
- Load balancing and availability

## Features

- **Intelligent Routing**: Subject and grade-based provider selection
- **Data Residency**: Enforces regional compliance requirements
- **Teacher Overrides**: Allows educators to specify preferred providers
- **Caching**: Redis-based response caching for performance
- **Statistics**: Comprehensive usage and performance metrics
- **Configuration**: Hot-reload of policy rules and settings

## API Endpoints

### Core Endpoints

- `POST /policy` - Get routing policy for given parameters
- `GET /health` - Service health check
- `GET /stats` - Usage statistics and metrics

### Override Management

- `POST /override` - Create teacher override
- `DELETE /override/{id}` - Remove teacher override

### Cache Management

- `POST /cache/clear` - Clear all cached policies
- `POST /cache/invalidate/subject/{subject}` - Invalidate subject cache
- `POST /cache/invalidate/region/{region}` - Invalidate region cache

### Administration

- `POST /config/reload` - Reload policy configuration

## Configuration

The service is configured via environment variables:

### Service Settings

- `SERVICE_NAME` - Service name (default: model-dispatch-svc)
- `SERVICE_VERSION` - Service version (default: 1.0.0)
- `HOST` - Bind address (default: 0.0.0.0)
- `PORT` - Port number (default: 8000)
- `DEBUG` - Enable debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)

### Cache Settings

- `CACHE_REDIS_URL` - Redis connection URL
- `CACHE_DEFAULT_TTL` - Default cache TTL in seconds
- `CACHE_ENABLED` - Enable caching (default: true)

### CORS Settings

- `CORS_ORIGINS` - Allowed origins (comma-separated)
- `CORS_CREDENTIALS` - Allow credentials (default: false)
- `CORS_METHODS` - Allowed methods (default: GET,POST,PUT,DELETE)
- `CORS_HEADERS` - Allowed headers (default: *)

## Request/Response Models

### Policy Request

```json
{
  "subject": "MATHEMATICS",
  "grade_band": "ELEMENTARY",
  "region": "US_WEST",
  "student_id": "student_123",
  "teacher_id": "teacher_456",
  "request_metadata": {}
}
```

### Policy Response

```json
{
  "provider": "OPENAI_GPT4",
  "endpoint": "https://api.openai.com/v1/chat/completions",
  "model_name": "gpt-4",
  "region": "US_WEST",
  "priority": 1,
  "reasoning": "Selected based on math expertise and regional preference",
  "data_residency_compliant": true,
  "cached": false,
  "expires_at": "2024-01-15T12:00:00Z"
}
```

## Development

### Local Setup

```bash
# Install dependencies
pip install -e .

# Start Redis (required for caching)
docker run -d -p 6379:6379 redis:7-alpine

# Run the service
python -m uvicorn app.main:app --reload
```

### Testing

```bash
# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=app
```

### Code Quality

```bash
# Format code
python -m ruff format app/

# Lint code
python -m ruff check app/
```

## Docker

### Build Image

```bash
docker build -t model-dispatch-svc .
```

### Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -e CACHE_REDIS_URL=redis://redis:6379 \
  --name model-dispatch-svc \
  model-dispatch-svc
```

## Policy Rules

The service uses a rule-based system to determine provider selection:

1. **Subject Expertise**: Providers are matched to their strongest subject areas
2. **Regional Compliance**: Data residency requirements filter available providers
3. **Grade Band Optimization**: Age-appropriate model selection
4. **Load Balancing**: Distributes load across available providers
5. **Teacher Overrides**: Manual selections take highest priority

### Default Rules

- Mathematics: Claude/GPT-4 preference
- Language Arts: GPT-4/Claude preference  
- Science: Claude/GPT-4 preference
- Social Studies: GPT-4/Claude preference
- Arts: Balanced distribution

## Monitoring

The service provides comprehensive metrics:

- Request volume and latency
- Provider distribution
- Cache hit/miss ratios
- Regional usage patterns
- Error rates and availability

## Data Residency

Enforces strict data residency policies:

- **US**: OpenAI, Anthropic (Claude)
- **EU**: Anthropic (Claude EU), OpenAI EU
- **APAC**: Regional compliance providers
- **Canada**: OpenAI, Anthropic with Canadian data centers

## Security

- Non-root container execution
- Environment-based configuration
- Request validation and sanitization
- Rate limiting and circuit breakers
- Audit logging for all decisions
