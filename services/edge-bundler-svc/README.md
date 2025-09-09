# Edge Bundler Service (S2A-09)

## Overview

The Edge Bundler Service provides **signed offline bundles with ≤50 MB
pre-cache** and CRDT merge hooks for seamless offline learning experiences.

## Key Features

### Bundle Management

- **Size Constraints**: Enforces ≤50MB total bundle size, ≤25MB precache budget
- **Compression**: Automatic tarball creation with gzip compression
- **Signing**: SHA256 checksums and bundle signing capability
- **Versioning**: Semantic versioning support with conflict detection

### CRDT Integration

- **Vector Clocks**: Distributed conflict resolution with last-writer-wins
- **Merge Operations**: Automatic conflict resolution for offline changes
- **Device Synchronization**: Multi-device state reconciliation
- **Audit Trail**: Complete merge history and conflict logs

### Offline Capabilities

- **Lesson Bundling**: Package lessons with assets for offline use
- **Adaptive Content**: Dynamic content selection based on device
  capabilities
- **Progressive Downloads**: Efficient incremental bundle updates
- **Cache Management**: Intelligent precache budget allocation

## API Endpoints

### Core Bundle Operations

- `POST /api/edge-bundler/v1/bundles` - Create new bundle
- `GET /api/edge-bundler/v1/bundles` - List bundles with pagination
- `GET /api/edge-bundler/v1/bundles/{id}` - Get bundle details
- `PUT /api/edge-bundler/v1/bundles/{id}` - Update bundle
- `DELETE /api/edge-bundler/v1/bundles/{id}` - Delete bundle

### Download Management

- `GET /api/edge-bundler/v1/bundles/{id}/download` - Download bundle
- `GET /api/edge-bundler/v1/bundles/{id}/download/signed-url` - Get signed
  download URL
- `GET /api/edge-bundler/v1/downloads/{id}/status` - Check download status

### CRDT Operations

- `POST /api/edge-bundler/v1/crdt/merge` - Merge CRDT states
- `GET /api/edge-bundler/v1/crdt/conflicts` - List unresolved conflicts
- `POST /api/edge-bundler/v1/crdt/resolve` - Resolve conflicts manually

### Statistics & Monitoring

- `GET /api/edge-bundler/v1/bundles/stats` - Bundle statistics
- `GET /api/edge-bundler/health` - Health check

## Bundle Structure

```json
{
  "id": "uuid",
  "title": "Lesson Bundle",
  "version": "1.0.0",
  "status": "ready",
  "total_size_mb": 45.2,
  "precache_budget_mb": 20.0,
  "compression_type": "gzip",
  "checksum": "sha256:...",
  "lessons": [
    {
      "lesson_id": "uuid",
      "content_url": "https://...",
      "assets": [...],
      "size_mb": 15.0
    }
  ],
  "metadata": {
    "target_devices": ["tablet", "phone"],
    "offline_duration_hours": 168,
    "crdt_vector_clock": {...}
  }
}
```

## Size Constraints

### Bundle Limits

- **Maximum Bundle Size**: 50MB total
- **Precache Budget**: ≤25MB for immediate availability
- **Asset Compression**: Automatic optimization for size
- **Progressive Loading**: Non-critical assets loaded on-demand

### Validation Rules

1. Total bundle size must not exceed 50MB
2. Precache content must not exceed 25MB
3. Individual lesson size should be reasonable for target devices
4. Asset formats optimized for compression

## CRDT Implementation

### Vector Clock Structure

```json
{
  "device_id": "device-123",
  "clock": {
    "device-123": 5,
    "device-456": 3,
    "device-789": 1
  },
  "last_modified": "2024-01-15T10:30:00Z"
}
```

### Conflict Resolution

- **Last Writer Wins**: Automatic resolution based on vector clocks
- **Manual Resolution**: Admin interface for complex conflicts
- **Merge Logs**: Complete audit trail of all merge operations
- **Rollback Support**: Ability to revert problematic merges

## Development

### Local Setup

```bash
cd services/edge-bundler-svc
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Running Tests

```bash
pytest tests/ -v
```

### Docker Build

```bash
docker build -t edge-bundler-svc .
docker run -p 8000:8000 edge-bundler-svc
```

## Configuration

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis cache connection
- `BUNDLE_STORAGE_PATH` - Local storage path for bundles
- `MAX_BUNDLE_SIZE_MB` - Maximum bundle size (default: 50)
- `MAX_PRECACHE_SIZE_MB` - Maximum precache size (default: 25)
- `SIGNING_KEY_PATH` - Path to bundle signing key

### Database Setup

```sql
-- Run migrations
alembic upgrade head
```

## Monitoring

### Health Checks

- Service health: `GET /api/edge-bundler/health`
- Database connectivity check
- Storage availability check
- CRDT consistency validation

### Metrics

- Bundle creation rate
- Download success rate
- CRDT merge frequency
- Storage utilization
- Compression efficiency

## Security

### Bundle Signing

- SHA256 checksums for integrity
- Optional cryptographic signatures
- Secure download URLs with expiration
- Access control for sensitive content

### Data Protection

- Encrypted storage for sensitive bundles
- Audit logs for all operations
- Rate limiting for API endpoints
- Input validation and sanitization

## Integration

### Dependencies

- **Lesson Registry Service**: Lesson metadata and content
- **Content Delivery Network**: Asset distribution
- **Device Management**: Device capabilities and constraints
- **Analytics Service**: Usage tracking and optimization

### Event Streaming

- Bundle creation events
- Download completion events
- CRDT merge notifications
- Conflict resolution alerts

---

**Status**: ✅ Fully Implemented  
**S2A-09 Requirements**: Complete with size constraints and CRDT hooks  
**Last Updated**: January 2024
