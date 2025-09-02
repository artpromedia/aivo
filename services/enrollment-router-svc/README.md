# Enrollment Router Service

A service that routes learner enrollments between district-provided seats
and parent-paid subscriptions based on availability and context.

## Overview

The Enrollment Router Service implements the S1-05 requirement to
intelligently route learner enrollments based on:

- **District Path**: If `context.tenantId` exists and FREE seats are
  available → reserve seat, set `provision_source='district'`
- **Parent Path**: Otherwise → set `provision_source='parent'` + return
  checkout URL for payment

## Core Features

### 🎯 Enrollment Routing

- **Intelligent Decision Logic**: Routes based on seat availability and context
- **District Seat Management**: Tracks and reserves district-provided seats
- **Parent Payment Integration**: Creates checkout sessions for parent-paid enrollments
- **Fallback Mechanism**: Falls back to parent payment when district seats unavailable

### 📊 Decision Tracking

- **Complete Audit Trail**: Records all enrollment decisions with full context
- **Event Publishing**: Emits `ENROLLMENT_DECISION` events for downstream processing
- **Status Tracking**: Monitors enrollment status from decision through completion
- **Metadata Storage**: Preserves learner profile and enrollment context

### 🏗️ Architecture

#### Database Models (`app/models.py`)

- **EnrollmentDecision**: Records routing decisions and outcomes
- **DistrictSeatAllocation**: Manages district seat allocations and usage

#### API Schemas (`app/schemas.py`)

- **EnrollmentRequest**: Input validation for enrollment routing
- **LearnerProfile**: Learner information and details
- **EnrollmentContext**: Context for routing decisions
- **Result Schemas**: Type-safe responses for different routing outcomes

#### Business Logic (`app/services.py`)

- **EnrollmentRouterService**: Main routing logic and orchestration
- **DistrictSeatService**: District seat allocation management
- **PaymentService**: Integration with payment service for checkout sessions
- **EventService**: Event publishing for decision notifications

### 🛠️ API Endpoints

#### Core Enrollment

- `POST /enroll` - Route learner enrollment based on context and availability
- `GET /enrollments/{decision_id}` - Get enrollment decision details
- `GET /enrollments` - List enrollment decisions with filtering

#### District Management

- `POST /districts/seats` - Create district seat allocation
- `GET /districts/{tenant_id}/seats` - Get district seat allocation
- `PUT /districts/{tenant_id}/seats` - Update district seat allocation
- `GET /districts` - List district allocations

#### Health Check

- `GET /health` - Service health status

### 📝 Usage Examples

#### District Enrollment

```json
POST /enroll
{
  "learner_profile": {
    "email": "student@school.edu",
    "first_name": "Jane",
    "last_name": "Doe",
    "grade_level": "3rd"
  },
  "context": {
    "tenant_id": 1,
    "source": "district_portal"
  }
}
```

**Response (District Path)**:

```json
{
  "provision_source": "district",
  "status": "completed",
  "tenant_id": 1,
  "seats_reserved": 1,
  "seats_available": 49,
  "decision_id": 123,
  "message": "Successfully enrolled via district allocation"
}
```

#### Parent Enrollment

```json
POST /enroll
{
  "learner_profile": {
    "email": "student@parent.com",
    "first_name": "John",
    "last_name": "Smith"
  },
  "context": {
    "guardian_id": "guardian_456",
    "source": "parent_portal"
  }
}
```

**Response (Parent Path)**:

```json
{
  "provision_source": "parent",
  "status": "checkout_required",
  "guardian_id": "guardian_456",
  "checkout_session_id": "cs_test_123",
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_123",
  "decision_id": 124,
  "message": "Checkout session created for parent payment"
}
```

### 🧪 Testing

Comprehensive test suite covering:

- **District Path Tests**: Seat availability, reservation, fallback scenarios
- **Parent Path Tests**: Checkout session creation, guardian handling
- **Audit Tests**: Decision recording, event publishing, metadata storage
- **API Integration Tests**: Full endpoint testing and validation

```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test categories
poetry run pytest tests/test_district_path.py -v
poetry run pytest tests/test_parent_path.py -v
poetry run pytest tests/test_audit.py -v
poetry run pytest tests/test_api.py -v
```

### 🚀 Development

#### Setup

```bash
cd services/enrollment-router-svc
poetry install
poetry run uvicorn app.main:app --reload --port 8002
```

#### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@localhost/enrollment_router
DEBUG=false
```

#### Database Setup

The service automatically creates tables on startup. For production
deployments, consider using proper database migrations.

### 🔄 Event Publishing

The service publishes `ENROLLMENT_DECISION` events containing:

```json
{
  "event_type": "ENROLLMENT_DECISION",
  "decision_id": 123,
  "provision_source": "district",
  "tenant_id": 1,
  "guardian_id": null,
  "learner_email": "student@school.edu",
  "status": "completed",
  "timestamp": "2025-09-02T10:30:00Z",
  "metadata": {
    "allocation_id": 1,
    "seats_reserved": 1
  }
}
```

### 🏭 Production Considerations

1. **Database Performance**: Index key lookup fields (tenant_id, guardian_id,
   learner_email)
2. **Event Publishing**: Replace logging with actual message queue (Redis,
   RabbitMQ, etc.)
3. **Rate Limiting**: Implement rate limiting for enrollment endpoints
4. **Caching**: Cache district seat allocations for performance
5. **Monitoring**: Add metrics for enrollment routing decisions and success
   rates

### 🔗 Integration

#### Payment Service

Integrates with the Payment Service (S1-04) for checkout session creation:

- Creates checkout sessions for parent-paid enrollments
- Includes learner metadata in payment context
- Handles payment service failures gracefully

#### Event Consumers

Other services can consume `ENROLLMENT_DECISION` events for:

- Learner account provisioning
- Parent/district notifications
- Analytics and reporting

---

**Implementation Status**: ✅ Complete - S1-05 Enrollment Router  
**Test Coverage**: Full test suite with district path, parent path, and audit
scenarios  
**Ready for**: Production deployment and integration with other services
