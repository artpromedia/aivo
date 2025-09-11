# Evidence Service (#S2B-04)

Extract keywords from uploads/recordings and attach evidence to IEP goals using AWS Textract and OpenAI Whisper with SHA-256 audit chains.

## Features

- **Document Processing**: AWS Textract for PDF, images with advanced analysis (tables, forms, key-value pairs)
- **Audio Processing**: OpenAI Whisper for transcription with large file chunking and multi-language support
- **Keyword Extraction**: Multi-method extraction using TF-IDF, YAKE, and spaCy with educational domain mappings
- **IEP Goal Linkage**: Sophisticated evidence-to-learning-objective connection with weighted similarity scoring
- **Audit Chain**: SHA-256 blockchain-style audit trail with RSA signatures for compliance
- **Teacher Validation**: Workflow for educators to validate AI-generated linkages

## Architecture

```
Evidence Service
 Extractors/
    Textract (Documents)
    Whisper (Audio)
 Processors/
    Keywords (TF-IDF, YAKE, spaCy)
    Audit Chain (SHA-256)
 Linkage/
     IEP Goals (Weighted Similarity)
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose
- AWS credentials (for Textract & S3)
- OpenAI API key (for Whisper)

### Environment Setup

1. **Clone and navigate:**
```bash
cd services/evidence-svc
```

2. **Set environment variables:**
```bash
export DATABASE_URL="postgresql+asyncpg://evidence_user:evidence_pass@localhost:5432/evidence_db"
export AWS_REGION="us-east-1"
export S3_BUCKET="evidence-uploads"
export OPENAI_API_KEY="your-openai-api-key"
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
# or using Poetry:
poetry install
```

4. **Download spaCy model:**
```bash
python -m spacy download en_core_web_sm
```

### Docker Setup

1. **Generate audit keys (optional):**
```bash
mkdir -p keys
openssl genrsa -out keys/audit_private.pem 2048
openssl rsa -in keys/audit_private.pem -pubout -out keys/audit_public.pem
```

2. **Start services:**
```bash
docker-compose up -d
```

3. **Create database tables:**
```bash
# In a Python shell or script:
from app.database import create_tables
import asyncio
asyncio.run(create_tables())
```

### Development Setup

1. **Start database:**
```bash
docker-compose up postgres -d
```

2. **Run development server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Access API docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Evidence Upload & Processing

- `POST /uploads` - Upload evidence file (document/audio)
- `GET /uploads/{upload_id}` - Get upload details
- `GET /uploads/{upload_id}/extraction` - Get extraction results
- `GET /uploads/{upload_id}/keywords` - Get keyword extraction
- `GET /uploads/{upload_id}/linkages` - Get IEP goal linkages

### IEP Goal Management

- `POST /iep-goals` - Create IEP goal
- `GET /learners/{learner_id}/iep-goals` - Get learner's goals
- `POST /linkages/{linkage_id}/validate` - Validate teacher linkage

### Audit & Compliance

- `GET /learners/{learner_id}/audit-trail` - Get audit trail
- `GET /learners/{learner_id}/audit-verification` - Verify chain integrity
- `GET /audit/statistics` - Get audit statistics

## Usage Examples

### 1. Upload Document Evidence

```python
import requests

# Upload a PDF document
with open("student_work.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/uploads",
        files={"file": f},
        data={
            "learner_id": "123e4567-e89b-12d3-a456-426614174000",
            "uploaded_by": "456e7890-e89b-12d3-a456-426614174000"
        }
    )

upload_info = response.json()
print(f"Uploaded: {upload_info['id']}")
```

### 2. Upload Audio Recording

```python
# Upload an audio recording
with open("class_discussion.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:8000/uploads",
        files={"file": f},
        data={
            "learner_id": "123e4567-e89b-12d3-a456-426614174000",
            "uploaded_by": "456e7890-e89b-12d3-a456-426614174000"
        }
    )
```

### 3. Create IEP Goal

```python
goal_data = {
    "learner_id": "123e4567-e89b-12d3-a456-426614174000",
    "goal_text": "Student will solve multi-step word problems involving addition and subtraction with 80% accuracy",
    "subject_area": "Mathematics",
    "goal_type": "Academic",
    "target_criteria": "80% accuracy on 4 out of 5 consecutive trials",
    "measurement_method": "Weekly assessments and work samples",
    "created_by": "456e7890-e89b-12d3-a456-426614174000"
}

response = requests.post("http://localhost:8000/iep-goals", json=goal_data)
```

### 4. Validate Evidence Linkage

```python
# Teacher validates an AI-generated linkage
response = requests.post(
    f"http://localhost:8000/linkages/{linkage_id}/validate",
    params={
        "is_valid": True,
        "validated_by": "teacher_user_id"
    }
)
```

## Subject Area Mappings

The service includes comprehensive educational domain knowledge:

- **Mathematics**: arithmetic, algebra, geometry, measurement, data analysis
- **English Language Arts**: reading, writing, speaking, listening, language
- **Science**: physical, life, earth, space, engineering
- **Social Studies**: history, geography, civics, economics
- **Special Education**: adaptive, behavioral, social, communication skills

## Processing Pipeline

1. **Upload**  File stored in S3, database record created
2. **Extract**  Textract/Whisper processes content
3. **Keywords**  Multi-method extraction with subject tagging
4. **Link**  Evidence matched to IEP goals using weighted similarity
5. **Audit**  SHA-256 chain entry created for compliance
6. **Validate**  Teachers review and confirm linkages

## Audit Chain Features

- **SHA-256 Hashing**: Content integrity verification
- **Chain Linkage**: Each entry links to previous hash
- **RSA Signatures**: Optional cryptographic signing
- **Verification**: Complete chain integrity checking
- **Export**: Compliance-ready audit trail export

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `AWS_REGION`: AWS region for Textract/S3
- `S3_BUCKET`: S3 bucket for file storage
- `OPENAI_API_KEY`: OpenAI API key for Whisper
- `AUDIT_PRIVATE_KEY_PATH`: RSA private key for signing
- `AUDIT_PUBLIC_KEY_PATH`: RSA public key for verification
- `DATABASE_ECHO`: Enable SQL query logging (development)

### Model Configuration

The service uses large dictionary configurations following PY LINT HYGIENE:
- Multi-line formatting with trailing commas
- Parentheses for line breaks under 100 columns
- Proper Ruff formatting compliance

## Development

### Code Quality

- **Linting**: Ruff with strict configuration
- **Type Checking**: mypy with strict mode
- **Testing**: pytest with async support
- **Documentation**: Comprehensive docstrings

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Test specific component
pytest tests/test_extractors.py -v
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Reset database (development)
python -c "
from app.database import reset_database
import asyncio
asyncio.run(reset_database())
"
```

## Production Deployment

### Security

- Use environment-specific database credentials
- Configure proper CORS origins
- Enable SSL/TLS for API endpoints
- Secure audit key storage (AWS KMS, HashiCorp Vault)
- Implement rate limiting and authentication

### Scaling

- Use task queues (Celery/RQ) for async processing
- Scale extractor workers based on upload volume
- Implement database read replicas for reporting
- Use Redis for caching and session management

### Monitoring

- Application metrics with Prometheus
- Log aggregation with ELK stack
- Health checks and alerting
- Audit chain verification monitoring

## Compliance

This service implements audit chains specifically designed for educational compliance:

- **FERPA**: Student data protection and access logging
- **IDEA**: IEP documentation and evidence tracking
- **State Standards**: Evidence linking to learning objectives
- **Data Integrity**: SHA-256 verification for legal requirements

## Support

For technical issues or feature requests, refer to the main project documentation or submit issues through the appropriate channels.

---

**Evidence Engineer Implementation**: This service fulfills requirement #S2B-04 with comprehensive evidence extraction, keyword analysis, IEP goal linkage, and SHA-256 audit chains for educational compliance.
