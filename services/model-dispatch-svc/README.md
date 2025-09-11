# Model Dispatch Service 

**#S2-09  Model Dispatch Policy  Policy Engineer**

LLM provider selection service with subject/grade/region policy enforcement and data residency compliance.

##  Features

- ** Subject/Grade/Region Policy**: Automatic provider selection based on educational context
- ** Data Residency**: Regional routing rules for compliance requirements  
- ** Teacher Override**: Manual provider selection with audit logging
- ** Analytics**: Dispatch metrics and performance tracking
- ** Security**: Rate limiting, moderation thresholds, and access controls
- ** Performance**: Optimized policy resolution with fallback chains

##  Architecture

```
Input: {subject, grade_band, region}
  
Policy Resolution Engine
  
Regional Compliance Check
  
Provider Selection
  
Output: {provider, templateIds, moderation_threshold}
```

### Policy Resolution Order

1. **Exact Match**: subject + grade_band + region
2. **Subject + Grade**: Any region  
3. **Subject Only**: Any grade/region
4. **Default Policy**: Fallback for unmatched requests

##  Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis (optional, for caching)

### Installation

```bash
cd services/model-dispatch-svc
poetry install
```

### Database Setup

```bash
# Create PostgreSQL database
createdb model_dispatch_db

# Set environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/model_dispatch_db"

# Run migrations (if using Alembic)
poetry run alembic upgrade head
```

### Start Service

```bash
poetry run start
# or
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

API Documentation: http://localhost:8002/docs

##  API Usage

### Basic Dispatch Request

```bash
curl -X POST "http://localhost:8002/dispatch?request_id=$(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "mathematics",
    "grade_band": "elementary", 
    "region": "us_east"
  }'
```

**Response:**
```json
{
  "provider_id": "550e8400-e29b-41d4-a716-446655440000",
  "provider_name": "OpenAI GPT-4",
  "endpoint_url": "https://api.openai.com/v1/chat/completions",
  "template_ids": ["123e4567-e89b-12d3-a456-426614174001"],
  "moderation_threshold": 0.8,
  "policy_id": "456e7890-e89b-12d3-a456-426614174002",
  "allow_teacher_override": true,
  "rate_limits": {
    "requests_per_minute": 60,
    "tokens_per_minute": 100000
  },
  "estimated_cost": {
    "per_1k_input_tokens": 0.03,
    "per_1k_output_tokens": 0.06
  }
}
```

### Teacher Override Request

```bash
curl -X POST "http://localhost:8002/dispatch?request_id=$(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "science",
    "grade_band": "high",
    "region": "eu_west", 
    "teacher_override": true,
    "override_provider_id": "550e8400-e29b-41d4-a716-446655440000",
    "override_reason": "Student needs specialized science model"
  }'
```

### Get Available Providers

```bash
curl "http://localhost:8002/providers?region=us_east"
```

### Validate Policy Exists

```bash
curl "http://localhost:8002/policies/validate?subject=mathematics&grade_band=elementary&region=africa_south"
```

##  Data Models

### Core Enums

```python
class Subject(str, Enum):
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    LANGUAGE_ARTS = "language_arts"
    SOCIAL_STUDIES = "social_studies"
    # ... more subjects

class GradeBand(str, Enum):
    EARLY_CHILDHOOD = "early_childhood"  # Pre-K to K
    ELEMENTARY = "elementary"            # Grades 1-5
    MIDDLE = "middle"                    # Grades 6-8
    HIGH = "high"                        # Grades 9-12
    ADULT = "adult"                      # Adult education
    SPECIAL = "special"                  # Special needs

class Region(str, Enum):
    US_EAST = "us_east"
    US_WEST = "us_west"
    EU_WEST = "eu_west"
    APAC_SINGAPORE = "apac_singapore"
    AFRICA_SOUTH = "africa_south"
    # ... more regions
```

### Database Tables

- **`model_providers`**: LLM provider configurations
- **`prompt_templates`**: Subject/grade-specific templates
- **`dispatch_policies`**: Policy rules for provider selection
- **`regional_routing`**: Data residency and compliance rules
- **`dispatch_logs`**: Audit trail of all dispatch decisions
- **`model_metrics`**: Performance metrics by provider/subject/grade/region

##  Regional Routing & Data Residency

### Supported Regions

| Region | Data Center | Compliance | Providers |
|--------|-------------|------------|-----------|
| **US East** | Virginia | FERPA, COPPA | OpenAI, Anthropic, Microsoft |
| **US West** | California | FERPA, COPPA | Google, AWS Bedrock |
| **EU West** | Ireland | GDPR | Local providers, EU-hosted |
| **APAC Singapore** | Singapore | PDPA | Regional providers |
| **Africa South** | Cape Town | POPIA | Local providers |

### Regional Constraints

```json
{
  "region": "eu_west",
  "data_residency_required": true,
  "encryption_required": true,
  "audit_logging_required": true,
  "allowed_providers": ["local-eu-provider"],
  "blocked_providers": ["us-only-provider"],
  "compliance_frameworks": ["GDPR", "ISO27001"]
}
```

##  Teacher Override Capabilities

Teachers can override policy decisions when:

- Policy allows teacher override (`allow_teacher_override: true`)
- Valid justification is provided
- Override provider is available in the region
- Compliance requirements are met

**Override Flow:**
1. Teacher selects alternative provider
2. Provides educational justification
3. System validates availability and compliance
4. Logs override decision for audit
5. Returns override provider configuration

##  Analytics & Monitoring

### Available Metrics

```bash
# Get dispatch analytics
curl "http://localhost:8002/analytics?region=us_east&days=30"
```

**Response:**
```json
{
  "total_requests": 15420,
  "success_rate": 0.998,
  "teacher_override_rate": 0.12,
  "most_used_subjects": {
    "mathematics": 4200,
    "science": 3800,
    "language_arts": 3600
  },
  "most_used_grades": {
    "elementary": 6500,
    "middle": 4200,
    "high": 3800
  },
  "average_response_time_ms": 245
}
```

### Performance Monitoring

- Response time tracking per provider
- Success/failure rates by region
- Cost analysis and optimization
- Teacher override patterns
- Policy effectiveness metrics

##  Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/model_dispatch_db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
METRICS_ENABLED=true
```

### Policy Configuration

```python
# Example dispatch policy
{
    "name": "Elementary Math - US East",
    "subject": "mathematics",
    "grade_band": "elementary", 
    "region": "us_east",
    "primary_provider_id": "openai-gpt4",
    "fallback_provider_ids": ["anthropic-claude", "microsoft-copilot"],
    "template_ids": ["math-elementary-basic", "math-word-problems"],
    "moderation_threshold": 0.8,
    "allow_teacher_override": true,
    "priority": 100
}
```

##  Development

### Code Quality (Ruff Lint Hygiene)

```bash
# Format code
poetry run ruff format .

# Lint code  
poetry run ruff check .

# Type checking
poetry run mypy app/
```

### Testing

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Test specific functionality
poetry run pytest tests/test_dispatch_service.py -v
```

### Pre-commit Hooks

```bash
# Install pre-commit
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

##  Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev
COPY . .
EXPOSE 8002
CMD ["poetry", "run", "start"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  model-dispatch:
    build: .
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/model_dispatch_db
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: model_dispatch_db
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

##  Security Considerations

- **Rate Limiting**: Per-provider and per-user limits
- **Input Validation**: Strict schema validation for all inputs
- **Audit Logging**: Complete trail of all dispatch decisions
- **Data Residency**: Enforcement of regional compliance requirements
- **Access Control**: Authentication and authorization (extend as needed)
- **Encryption**: In-transit and at-rest data encryption

##  Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/enhanced-policy-engine`
3. Follow lint hygiene with ruff formatting
4. Add tests for new functionality
5. Submit pull request

### Code Style

- **Line Length**: 100 characters max
- **Formatting**: Use ruff format
- **Imports**: Organized with ruff
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for all public methods

##  License

MIT License - See LICENSE file for details.

---

**feat(model-dispatch): subject/grade/region policy** 
