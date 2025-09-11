# Consent & Preferences Ledger

## #S2B-08  Centralized consent for data/media/chat; parental rights (export/delete 10 days)

A GDPR/COPPA compliant consent management system that centralizes consent tracking across multiple systems with parental rights support and cascaded data operations.

### Features

- **Centralized Consent Management**: Unified consent tracking across data/media/chat systems
- **GDPR Compliance**: Article 20 data portability with 10 days export requirement
- **COPPA Compliance**: Parental verification and consent management for users under 13
- **Cascaded Operations**: Multi-system data export and deletion (PostgreSQL, MongoDB, S3, Snowflake)
- **Audit Trail**: Tamper-evident audit logging with integrity protection
- **Privacy by Design**: Helper functions for clean code organization and secure operations

### Architecture

```
services/consent-ledger-svc/
 app/
    models/          # SQLAlchemy 2.0 models for consent tracking
    services/        # Core business logic services
    api/            # FastAPI routers for Ledger APIs
    tasks.py        # Celery background tasks
 config/             # Configuration management
 main.py            # FastAPI application
 pyproject.toml     # Poetry dependencies
```

### Core Services

#### Consent Management (`app/services/consent_service.py`)
- Create, update, and withdraw consent records
- COPPA age verification and parental consent workflows
- Consent validity checking for specific purposes
- Version tracking and audit logging

#### Parental Rights (`app/services/consent_service.py`)
- Parental verification via email tokens
- Parent-managed consent for children under 13
- Expiration and renewal of parental rights
- COPPA compliance enforcement

#### Data Export (`app/services/data_export.py`)
- GDPR Article 20 data portability
- Multi-format exports (JSON, CSV, ZIP)
- 10 days completion requirement monitoring
- Automatic file cleanup and retention management

#### Cascaded Deletion (`app/services/cascade_delete.py`)
- GDPR Article 17 right to erasure
- Multi-system deletion coordination
- Verification workflows with delay safeguards
- Progress tracking and failure handling

### API Endpoints

#### Consent Management (`/api/v1/consent`)
- `POST /` - Create consent record
- `GET /user/{user_id}` - Get user consents
- `PUT /{consent_id}` - Update consent
- `DELETE /{consent_id}` - Withdraw consent
- `GET /user/{user_id}/status` - Check consent validity

#### Parental Rights (`/api/v1/parental`)
- `POST /verify` - Initiate parental verification
- `POST /verify/{token}` - Complete verification
- `GET /child/{child_user_id}` - Get parental rights
- `POST /{right_id}/consent` - Manage child consent

#### Data Export (`/api/v1/export`)
- `POST /` - Create export request
- `GET /user/{user_id}` - Get user exports
- `GET /{export_id}/download` - Download export file
- `GET /stats/summary` - Export statistics

#### Data Deletion (`/api/v1/deletion`)
- `POST /` - Create deletion request
- `GET /{deletion_id}/systems` - System deletion status
- `POST /{deletion_id}/verify` - Verify deletion
- `POST /bulk` - Bulk deletion requests

### Setup

1. **Install Dependencies**
   ```bash
   poetry install
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Update .env with your configuration
   ```

3. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb consent_db
   
   # Run migrations (auto-created on startup)
   poetry run python main.py
   ```

4. **Start Services**
   ```bash
   # Start Redis
   redis-server
   
   # Start Celery worker
   poetry run celery -A app.tasks worker --loglevel=info
   
   # Start Celery beat (scheduler)
   poetry run celery -A app.tasks beat --loglevel=info
   
   # Start FastAPI application
   poetry run python main.py
   ```

### Code Quality

- **Helper Functions**: Short helper functions throughout to avoid long conditions
- **Import Organization**: `__all__` declarations in `__init__.py` files for clean imports
- **Async/Await**: Proper async patterns for database and external service operations
- **Type Hints**: Comprehensive type annotations for better code clarity
- **Error Handling**: Graceful error handling with proper HTTP status codes

### Compliance Features

#### GDPR Compliance
- **Article 20**: Data portability with 10 days completion
- **Article 17**: Right to erasure with cascaded deletion
- **Article 7**: Consent withdrawal capabilities
- **Audit Requirements**: Tamper-evident audit logs with 7-year retention

#### COPPA Compliance
- **Age Verification**: Automatic detection of users under 13
- **Parental Consent**: Email-based verification workflows
- **Parental Rights**: Parent-managed consent for children
- **Verification Expiry**: Token and rights expiration management

### Multi-System Integration

The service integrates with multiple data systems for cascaded operations:

- **PostgreSQL**: Primary consent database
- **MongoDB**: Document-based user data
- **Amazon S3**: File storage and media
- **Snowflake**: Data warehouse and analytics

### Background Processing

Celery tasks handle long-running operations:

- **Data Export Processing**: Multi-system data collection and formatting
- **Cascaded Deletion**: Coordinated deletion across all systems
- **Maintenance Tasks**: Export cleanup and deadline monitoring
- **Verification Tasks**: Deletion completion verification

### Monitoring & Health

- **Health Checks**: Database connectivity and service status
- **Metrics**: Export/deletion statistics and performance monitoring
- **Audit Logs**: Comprehensive audit trail for all consent operations
- **Error Tracking**: Structured error logging with retry mechanisms

### Security

- **Token Security**: Secure token generation for verification workflows
- **Audit Integrity**: Hash-based tamper detection for audit logs
- **Encryption**: Optional audit log encryption for sensitive data
- **Rate Limiting**: API rate limiting to prevent abuse

---

**Privacy Engineer Implementation**: Complete consent ledger with unified consent management, parental rights (COPPA), cascaded deletes to S3/PG/Mongo/Snowflake, audit trails, and 10 days export/delete compliance.
