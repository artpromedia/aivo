# Tenant Service

Multi-tenant service for managing districts, schools, and seat allocation in
the Aivo platform.

## Features

- **District Management**: Create and manage educational districts
- **School Management**: Create schools under districts with hierarchical relationships
- **Seat Lifecycle**: Purchase, allocate, and reclaim seats for learners
- **User Roles**: Assign roles to users within specific tenants (RBAC)
- **Audit Trail**: Complete audit trail for all seat state changes
- **Seat Analytics**: Real-time seat utilization summaries and counters

## Architecture

### Database Schema

#### Tenants

- `tenant`: Districts and schools with hierarchical parent-child relationships
- `user_tenant_role`: Role-based access control within tenants

#### Seats

- `seat`: Individual seats that can be allocated to learners
- `seat_audit`: Complete audit trail of seat state changes

### API Endpoints

#### Districts & Schools

- `POST /api/v1/district` - Create a new district
- `GET /api/v1/district/{id}` - Get district with schools
- `POST /api/v1/district/{id}/schools` - Create school under district

#### Seat Management

- `POST /api/v1/seats/purchase` - Purchase seats for a tenant
- `POST /api/v1/seats/allocate` - Allocate seat to learner
- `POST /api/v1/seats/reclaim` - Reclaim seat from learner
- `GET /api/v1/seats/summary?tenantId=X` - Get seat utilization summary

#### User Roles

- `POST /api/v1/roles` - Assign user role within tenant
- `GET /api/v1/users/{id}/tenants` - Get user's tenant roles

## Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run database migrations (if using Alembic)
alembic upgrade head

# Start the service
uvicorn app.main:app --reload --port 8001
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_tenant_seats.py -v
```

### Key Test Scenarios

- **Idempotent Allocation**: Learners cannot have multiple seats in same tenant
- **Seat State Transitions**: FREE → ASSIGNED → FREE with audit trail
- **Rollback Scenarios**: Proper error handling and state consistency
- **Hierarchy Validation**: Schools must belong to valid districts
- **Audit Compliance**: All seat changes create audit entries

## Business Rules

### Seat Allocation

1. Each learner can only have one seat per tenant
2. Seats must be FREE to be allocated
3. All state changes create audit entries
4. Seat counters are maintained in real-time

### Tenant Hierarchy

1. Districts are top-level tenants (parent_id = NULL)
2. Schools must have a district as parent
3. Seat allocation happens at the school level

### Role-Based Access

1. Users can have different roles in different tenants
2. Role assignments are tenant-specific
3. Inactive roles are preserved for audit

## Monitoring

- Health check: `GET /health`
- Service metrics: Seat utilization, allocation rates
- Audit compliance: Complete trail of all seat changes

## Production Considerations

- Database indexing on tenant_id, learner_id, state columns
- Connection pooling for high-concurrency scenarios
- Seat counter caching for performance
- Audit log retention policies
