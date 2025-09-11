# Compliance Export Service

State-format exports (EDFacts, CALPADS) with audit logs and encryption at rest.

## Features

- ** State Compliance**: EDFacts and CALPADS export formats
- ** Encryption at Rest**: AES encryption for all export files
- ** Immutable Audit Logs**: Tamper-evident compliance audit trails
- ** RPO/RTO 5 min**: Fast background processing with Celery
- ** Admin Dashboard**: Web interface for export management
- ** Data Validation**: Pre-export validation for compliance
- ** Progress Tracking**: Real-time export job monitoring

## CSV Header Lint Hygiene

Following PY LINT HYGIENE requirements, all CSV headers are broken across multiple lines:

```python
#  Good - Headers split across lines
EDFACTS_STUDENT_HEADERS = [
    "state_student_id",
    "district_id", 
    "school_id",
    "first_name",
    "middle_name",
    "last_name",
    # ... continues across multiple lines
]

# Use with csv.DictWriter
writer = csv.DictWriter(
    csvfile,
    fieldnames=EDFACTS_STUDENT_HEADERS,
    quoting=csv.QUOTE_MINIMAL,
)
```

## Quick Start

### 1. Installation

```bash
cd services/compliance-export-svc
poetry install
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Required environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/compliance_db"
export REDIS_URL="redis://localhost:6379/0"
export COMPLIANCE_MASTER_KEY="your-secure-master-key"
export COMPLIANCE_EXPORT_PATH="/secure/export/path"
```

### 3. Start Services

```bash
# Start FastAPI application
make run

# Start Celery worker (separate terminal)
celery -A app.jobs worker --loglevel=info

# Start Celery beat (separate terminal)
celery -A app.jobs beat --loglevel=info
```

### 4. Access Admin Dashboard

Open http://localhost:8000 for the admin dashboard.

## API Usage

### Create Export Job

```bash
curl -X POST "http://localhost:8000/api/exports" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "edfacts",
    "name": "Student Enrollment Export",
    "school_year": "2023-24",
    "state_code": "CA",
    "district_id": "001",
    "parameters": {
      "export_type": "student"
    }
  }'
```

### Check Job Status

```bash
curl "http://localhost:8000/api/exports/{job_id}"
```

### Download Export File

```bash
curl -O "http://localhost:8000/api/exports/{job_id}/download"
```

## Export Formats

### EDFacts (Federal)

- **Student Enrollment**: Demographic and enrollment data
- **Assessment Results**: Test scores and performance levels
- **Discipline Incidents**: Disciplinary actions and removals

#### EDFacts CSV Headers

```python
EDFACTS_STUDENT_HEADERS = [
    "state_student_id",
    "district_id",
    "school_id",
    "first_name",
    "middle_name",
    "last_name",
    "birth_date",
    "grade_level",
    "enrollment_status",
    "entry_date",
    "exit_date",
    "exit_reason",
    "gender",
    "race_ethnicity_hispanic",
    "race_ethnicity_american_indian",
    "race_ethnicity_asian",
    "race_ethnicity_black",
    "race_ethnicity_pacific_islander",
    "race_ethnicity_white",
    "race_ethnicity_two_or_more",
    "english_learner_status",
    "english_learner_entry_date",
    "english_learner_exit_date",
    "title_i_status",
    "migrant_status",
    "homeless_status",
    "foster_care_status",
    "military_connected_status",
    "immigrant_status",
    "idea_indicator",
    "idea_educational_environment",
    "idea_primary_disability",
    "idea_secondary_disability",
    "section_504_status",
    "gifted_talented_status",
    "ctae_participant",
    "ctae_concentrator",
    "neglected_delinquent_status",
    "perkins_english_learner",
    "title_iii_immigrant",
    "title_iii_language_instruction",
    "academic_year",
]
```

### CALPADS (California)

- **SENR**: Student Enrollment data
- **SASS**: Student Assessment data  
- **SDIS**: Student Discipline data

#### CALPADS SENR Headers

```python
CALPADS_SENR_HEADERS = [
    "academic_year",
    "district_code",
    "school_code",
    "student_id",
    "local_student_id",
    "student_legal_first_name",
    "student_legal_middle_name",
    "student_legal_last_name",
    "student_name_suffix",
    "student_birth_date",
    "student_gender",
    "student_birth_state_province",
    "student_birth_country",
    "student_primary_language",
    "student_correspondence_language",
    # ... continues with 40+ fields
]
```

## Security Features

### AES Encryption at Rest

All export files are encrypted using AES-256:

```python
from app.crypto import encryption_manager

# Generate file encryption key
key_id, key_data = encryption_manager.generate_file_key()

# Encrypt export file
encrypted_size = encryption_manager.encrypt_file(
    input_path, output_path, key_data
)

# Validate encryption
is_valid = encryption_manager.validate_encryption(output_path, key_data)
```

### Immutable Audit Logs

Every export operation is logged with tamper-evident integrity hashes:

```python
from app.audit import AuditLogger

audit_logger = AuditLogger(db_session)

# Log export creation
await audit_logger.log_export_created(export_job, user_id)

# Log file download
await audit_logger.log_export_downloaded(job_id, user_id)

# Generate audit report
report = await audit_logger.generate_audit_report(
    start_date=start_date,
    end_date=end_date,
)
```

## Background Processing

### Celery Configuration

Jobs are processed asynchronously with RPO/RTO 5 minutes:

```python
# Queue routing
CELERY_TASK_ROUTES = {
    "app.jobs.process_compliance_export": {"queue": "exports"},
    "app.jobs.validate_export_data": {"queue": "validation"},
    "app.jobs.cleanup_old_exports": {"queue": "maintenance"},
}

# Retry configuration
CELERY_TASK_DEFAULT_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60
```

### Job Processing

```python
from app.jobs import process_compliance_export

# Start export job
result = process_compliance_export.delay(
    job_id="uuid-string",
    format_type="edfacts",
    export_params={"export_type": "student"},
    user_id="admin@district.edu",
)

# Check job status
status = result.status
result_data = result.get() if result.ready() else None
```

## Data Validation

Pre-export validation ensures compliance:

```bash
curl -X POST "http://localhost:8000/api/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "format_type": "edfacts",
    "data_type": "student",
    "school_year": "2023-24",
    "district_id": "001"
  }'
```

Response:
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Some students missing phone numbers"],
  "record_counts": {
    "students": 1500,
    "enrollments": 1500
  }
}
```

## Database Models

### Export Job

```python
class ExportJob(Base):
    id: UUID = primary_key
    format: ExportFormat  # edfacts, calpads
    status: ExportStatus  # pending, running, completed, failed
    name: str
    school_year: str
    state_code: str
    created_at: datetime
    file_path: Optional[str]
    encrypted_file_path: Optional[str]
    encryption_key_id: Optional[str]
    progress_percentage: int
    total_records: Optional[int]
    processed_records: Optional[int]
```

### Audit Log

```python
class AuditLog(Base):
    id: UUID = primary_key
    export_job_id: UUID = foreign_key
    action: AuditAction  # export_created, export_completed, etc.
    timestamp: datetime
    user_id: str
    ip_address: Optional[str]
    details: Dict[str, Any]
    integrity_hash: str  # For tamper detection
```

## Maintenance

### Cleanup Old Exports

```bash
# Clean up exports older than 30 days
curl -X POST "http://localhost:8000/api/cleanup?retention_days=30"
```

### Generate Audit Report

```bash
curl -X POST "http://localhost:8000/api/reports/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T23:59:59",
    "format_type": "edfacts"
  }'
```

## Development

### Run Code Quality Checks

```bash
# Run all quality checks (py-fix target)
make py-fix

# Individual checks
make format    # Black + isort
make lint      # Flake8
make type-check # MyPy
make test      # Pytest
```

### Project Structure

```
services/compliance-export-svc/
 app/
    __init__.py
    main.py              # FastAPI application
    models.py            # SQLAlchemy models
    jobs.py              # Celery tasks
    audit.py             # Audit logging
    crypto.py            # AES encryption
    exporters/
        __init__.py
        edfacts.py       # EDFacts exporter
        calpads.py       # CALPADS exporter
 config/
    __init__.py
    settings.py          # Configuration management
 Makefile                 # Build system with py-fix
 pyproject.toml           # Poetry dependencies
 README.md               # This file
```

## Deployment

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/compliance_db
REDIS_URL=redis://localhost:6379/0
COMPLIANCE_MASTER_KEY=your-secure-master-key-32-chars

# Optional
COMPLIANCE_EXPORT_PATH=/secure/export/path
EXPORT_RETENTION_DAYS=90
LOG_LEVEL=INFO
MAX_CONCURRENT_EXPORTS=5
AUDIT_LOG_RETENTION_YEARS=7
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --only=main

COPY . .
EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Service Health

```bash
# Health check
curl http://localhost:8000/api/health

# Statistics
curl http://localhost:8000/api/stats
```

## Compliance

- ** EDFacts**: Federal reporting requirements
- ** CALPADS**: California state reporting
- ** FERPA**: Student privacy protection
- ** Audit Trails**: Immutable compliance logs
- ** Encryption**: AES-256 data protection
- ** RPO/RTO**: 5 minute recovery objectives

---

**Tech Stack**: FastAPI  SQLAlchemy 2.0  Celery  Redis  PostgreSQL  AES Encryption  Structured Logging
