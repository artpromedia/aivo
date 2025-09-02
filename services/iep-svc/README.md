# IEP Service

A GraphQL-based IEP (Individualized Education Program) document management
service with CRDT collaborative editing and dual approval workflow.

## Features

- **GraphQL API**: Strawberry GraphQL with FastAPI integration
- **CRDT Document Management**: Conflict-free collaborative editing
- **Dual Approval Workflow**: Integration with approval-svc for two-stage
  approval process
- **Real-time Synchronization**: Vector clock-based operation synchronization
- **Event Publishing**: Comprehensive event emission for document lifecycle
- **Comprehensive Validation**: IEP completeness validation before approval

## GraphQL Schema

### Core Types

- **IepDoc**: Main IEP document with student information, goals, and
  accommodations
- **Goal**: Individual educational goals with progress tracking
- **Accommodation**: Instructional and assessment accommodations
- **ApprovalRecord**: Dual approval workflow tracking

### Queries

- `iep(id: String!)`: Get IEP document by ID
- `ieps(studentId: String)`: List IEP documents, optionally by student
- `studentIeps(studentId: String!)`: Get all IEPs for a specific student
- `activeIeps()`: Get all active IEP documents
- `pendingApprovals()`: Get IEPs pending approval

### Mutations

- `createIep(input: IepDocInput!, createdBy: String!)`: Create new IEP document
- `saveDraft(iepId: String!, operations: [CrdtOperation!]!, updatedBy: String!)`:
  Save draft changes using CRDT operations
- `submitForApproval(iepId: String!, submittedBy: String!)`: Submit IEP for
  dual approval
- `addGoal(iepId: String!, goal: GoalInput!, addedBy: String!)`: Add goal to IEP
- `addAccommodation(iepId: String!, accommodation: AccommodationInput!,
  addedBy: String!)`: Add accommodation to IEP

## Installation

1. **Install Dependencies**:

   ```bash
   cd services/iep-svc
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the Service**:

   ```bash
   python run.py
   # Or with custom settings:
   python run.py --host 0.0.0.0 --port 8001 --reload --debug
   ```

4. **Run Tests**:

   ```bash
   python -m pytest tests/ -v
   ```

## Configuration

Environment variables (see `.env.example`):

- `IEP_HOST`: Server host (default: localhost)
- `IEP_PORT`: Server port (default: 8000)
- `IEP_DEBUG`: Debug mode (default: true)
- `IEP_LOG_LEVEL`: Logging level (default: INFO)
- `IEP_GRAPHQL_PATH`: GraphQL endpoint path (default: /graphql)
- `IEP_GRAPHIQL_ENABLED`: Enable GraphiQL interface (default: true)
- `IEP_APPROVAL_SERVICE_URL`: Approval service URL
- `IEP_EVENT_ENDPOINT`: Event publishing endpoint
- `IEP_DUAL_APPROVAL_REQUIRED`: Require dual approval (default: true)

## API Usage

### Creating an IEP Document

```graphql
mutation CreateIEP {
  createIep(
    input: {
      studentId: "student_123"
      studentName: "John Doe"
      schoolYear: "2024-2025"
      effectiveDate: "2024-09-01"
      expiryDate: "2025-08-31"
      presentLevels: "Student demonstrates..."
      goals: [
        {
          goalType: ACADEMIC
          title: "Reading Comprehension"
          description: "Improve reading skills"
          measurableCriteria: "80% accuracy"
          targetDate: "2025-06-01"
        }
      ]
      accommodations: [
        {
          accommodationType: INSTRUCTIONAL
          title: "Extended Time"
          description: "50% additional time"
        }
      ]
    }
    createdBy: "teacher_123"
  ) {
    success
    message
    iep {
      id
      studentName
      status
      goals {
        title
        goalType
      }
      accommodations {
        title
        accommodationType
      }
    }
  }
}
```

### Saving Draft Changes with CRDT

```graphql
mutation SaveDraft {
  saveDraft(
    iepId: "iep_123"
    operations: [
      {
        operationType: "update"
        path: "present_levels"
        value: "Updated present levels content"
        author: "teacher_123"
        timestamp: "2025-01-02T10:00:00Z"
      }
    ]
    updatedBy: "teacher_123"
  ) {
    success
    message
    iep {
      presentLevels
      version
    }
  }
}
```

### Submitting for Approval

```graphql
mutation SubmitForApproval {
  submitForApproval(iepId: "iep_123", submittedBy: "teacher_123") {
    success
    message
    approvalId
    status
  }
}
```

## CRDT Operations

The service uses Conflict-free Replicated Data Types (CRDT) for collaborative
editing. Supported operations:

### Update Operations

```json
{
  "operationType": "update",
  "path": "present_levels",
  "value": "New content",
  "author": "user_id",
  "timestamp": "2025-01-02T10:00:00Z"
}
```

### Insert Operations

```json
{
  "operationType": "insert",
  "path": "goals",
  "value": "{\"goalType\":\"academic\",\"title\":\"New Goal\"}",
  "position": 0,
  "author": "user_id",
  "timestamp": "2025-01-02T10:00:00Z"
}
```

### Delete Operations

```json
{
  "operationType": "delete",
  "path": "special_factors",
  "position": 1,
  "author": "user_id",
  "timestamp": "2025-01-02T10:00:00Z"
}
```

## Approval Workflow

1. **Draft Creation**: IEP created in draft status
2. **Collaborative Editing**: Multiple users can edit using CRDT operations
3. **Submission**: Complete IEP submitted for dual approval
4. **Approval Process**: Two approvers required (coordinator + administrator)
5. **Finalization**: Approved IEP becomes active, triggers `IEP_UPDATED` event

## Events

The service publishes events for:

- **IEP_CREATED**: When new IEP is created
- **IEP_UPDATED**: When IEP is modified (including final approval)
- **IEP_SUBMITTED**: When IEP is submitted for approval
- **IEP_APPROVED**: When IEP receives full approval
- **IEP_REJECTED**: When IEP approval is rejected
- **GOAL_ADDED**: When goal is added to IEP
- **GOAL_UPDATED**: When goal is modified
- **ACCOMMODATION_ADDED**: When accommodation is added

### Event Payload Example

```json
{
  "event_type": "IEP_UPDATED",
  "event_id": "evt_123",
  "timestamp": "2025-01-02T10:15:00Z",
  "service": "iep-svc",
  "resource_type": "iep_document",
  "resource_id": "iep_123",
  "user_id": "system",
  "data": {
    "student_id": "student_123",
    "status": "approved",
    "changes": ["status", "approval_records"],
    "updated_at": "2025-01-02T10:15:00Z"
  }
}
```

## Development

### Project Structure

```text
iep-svc/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── enums.py             # Enums (IepStatus, GoalType, etc.)
│   ├── schema.py            # GraphQL schema types
│   ├── resolvers.py         # GraphQL resolvers
│   ├── crdt_manager.py      # CRDT document management
│   ├── approval_service.py  # Approval workflow integration
│   └── event_service.py     # Event publishing
├── tests/
│   ├── __init__.py
│   └── test_iep_service.py  # Comprehensive test suite
├── pyproject.toml           # Poetry configuration
├── requirements.txt         # Pip requirements
├── .env.example            # Environment variables template
├── run.py                  # Startup script
└── README.md               # This file
```

### Testing

The test suite includes:

- ✅ GraphQL query and mutation testing
- ✅ CRDT operation validation
- ✅ Approval workflow simulation
- ✅ Event publishing verification
- ✅ Concurrent editing scenarios
- ✅ Error handling validation
- ✅ Webhook processing tests

Run tests with coverage:

```bash
python -m pytest tests/ -v --cov=app --cov-report=html
```

### GraphQL Development

Access GraphiQL interface at `http://localhost:8000/graphql` when
`IEP_GRAPHIQL_ENABLED=true`.

View schema documentation at `http://localhost:8000/schema`.

## Integration

### Approval Service Integration

The service integrates with `approval-svc` for dual approval workflow:

- Submits approval requests with IEP metadata
- Receives webhook notifications for approval status changes
- Updates IEP status based on approval outcomes

### Event Publishing

Events are published to the configured event endpoint for:

- Document lifecycle tracking
- Integration with other services
- Audit trail maintenance
- Real-time notifications

## License

See the main project LICENSE file.
