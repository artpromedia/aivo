# SCIM Service

SCIM 2.0 (System for Cross-domain Identity Management) provisioning service for enterprise identity management and automated user/group provisioning.

## Overview

The SCIM service provides enterprise-grade user and group provisioning capabilities following the SCIM 2.0 RFC specifications. It enables automated identity lifecycle management with external identity providers and HR systems.

## Features

### Core SCIM 2.0 Support

- **User Resource Management**: Complete CRUD operations for users with enterprise schema support
- **Group Resource Management**: Group lifecycle management with membership operations  
- **Bulk Operations**: Efficient bulk user/group provisioning and updates
- **Filtering & Search**: Advanced query capabilities with SCIM filter expressions
- **Schema Discovery**: Dynamic schema endpoint for client integration
- **Resource Types**: Extensible resource type definitions

### Enterprise Integration

- **Multi-tenant Architecture**: Isolated provisioning per tenant with custom schemas
- **Webhook Notifications**: Real-time event notifications for provisioning actions
- **Audit Logging**: Comprehensive audit trail for compliance and monitoring
- **Rate Limiting**: Configurable rate limits per tenant and endpoint
- **Authentication**: Bearer token and OAuth 2.0 authentication support

### Advanced Capabilities

- **Custom Attributes**: Extensible user/group schemas with custom enterprise attributes
- **Conflict Resolution**: Intelligent handling of duplicate users and data conflicts
- **Sync Status Tracking**: Real-time status of provisioning operations
- **Data Validation**: Comprehensive validation with business rule enforcement
- **Retry Logic**: Automatic retry for failed provisioning operations

## API Endpoints

### Service Discovery

```http
GET  /scim/v2/ServiceProviderConfig    # Service capabilities
GET  /scim/v2/ResourceTypes           # Available resource types  
GET  /scim/v2/Schemas                 # Supported schemas
```

### User Management

```http
GET    /scim/v2/Users                 # List users with filtering
GET    /scim/v2/Users/{id}            # Get specific user
POST   /scim/v2/Users                 # Create user
PUT    /scim/v2/Users/{id}            # Replace user
PATCH  /scim/v2/Users/{id}            # Update user attributes
DELETE /scim/v2/Users/{id}            # Deactivate/delete user
```

### Group Management

```http
GET    /scim/v2/Groups                # List groups with filtering
GET    /scim/v2/Groups/{id}           # Get specific group
POST   /scim/v2/Groups                # Create group
PUT    /scim/v2/Groups/{id}           # Replace group
PATCH  /scim/v2/Groups/{id}           # Update group/membership
DELETE /scim/v2/Groups/{id}           # Delete group
```

### Bulk Operations

```http
POST   /scim/v2/Bulk                  # Bulk user/group operations
GET    /scim/v2/Bulk/{id}/status      # Get bulk operation status
```

## Configuration

### Environment Variables

```bash
# Service Configuration
SCIM_SERVICE_PORT=8002
SCIM_SERVICE_HOST=0.0.0.0
SCIM_BASE_URL=https://api.aivo.com/scim/v2

# Database
DATABASE_URL=postgresql+asyncpg://scim_user:password@localhost:5432/scim_db
REDIS_URL=redis://localhost:6379/1

# Authentication
SCIM_BEARER_TOKEN=your-bearer-token
OAUTH_CLIENT_ID=your-oauth-client-id
OAUTH_CLIENT_SECRET=your-oauth-client-secret

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=1000
RATE_LIMIT_BURST_SIZE=100

# Webhook Configuration
WEBHOOK_BASE_URL=https://your-app.com/webhooks
WEBHOOK_SECRET=your-webhook-secret
```

### Multi-tenant Configuration

```yaml
tenants:
  tenant-1:
    name: "Acme Corp"
    bearer_token: "acme-bearer-token"
    custom_schemas:
      - "urn:acme:schemas:User"
      - "urn:acme:schemas:Department" 
    webhook_url: "https://acme.com/scim-webhook"
    
  tenant-2:
    name: "Global Inc"
    bearer_token: "global-bearer-token"
    custom_schemas:
      - "urn:global:schemas:Employee"
    webhook_url: "https://global.com/identity-webhook"
```

## SCIM Schema Examples

### User Resource

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "id": "2819c223-7f76-453a-919d-413861904646",
  "externalId": "emp12345",
  "userName": "john.doe@acme.com",
  "name": {
    "formatted": "John Doe",
    "familyName": "Doe",
    "givenName": "John"
  },
  "emails": [
    {
      "value": "john.doe@acme.com",
      "type": "work",
      "primary": true
    }
  ],
  "active": true,
  "groups": [
    {
      "value": "e9e30dba-f08f-4109-8486-d5c6a331660a",
      "ref": "Groups/e9e30dba-f08f-4109-8486-d5c6a331660a",
      "display": "Engineering"
    }
  ],
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
    "employeeNumber": "12345",
    "department": "Engineering",
    "manager": {
      "value": "26118915-6090-4610-87e4-49d8ca9f808d",
      "ref": "Users/26118915-6090-4610-87e4-49d8ca9f808d"
    }
  }
}
```

### Group Resource

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "id": "e9e30dba-f08f-4109-8486-d5c6a331660a",
  "displayName": "Engineering",
  "members": [
    {
      "value": "2819c223-7f76-453a-919d-413861904646",
      "ref": "Users/2819c223-7f76-453a-919d-413861904646",
      "type": "User"
    }
  ]
}
```

## Filtering and Search

### User Filtering Examples

```http
# Filter by username
GET /scim/v2/Users?filter=userName eq "john.doe@acme.com"

# Filter by active status
GET /scim/v2/Users?filter=active eq true

# Complex filter with AND/OR
GET /scim/v2/Users?filter=active eq true and (emails co "@acme.com" or emails co "@global.com")

# Filter by group membership
GET /scim/v2/Users?filter=groups.display eq "Engineering"

# Sort and paginate
GET /scim/v2/Users?sortBy=userName&sortOrder=ascending&startIndex=1&count=50
```

### Group Filtering Examples

```http
# Filter by display name
GET /scim/v2/Groups?filter=displayName co "Engineering"

# Filter by member
GET /scim/v2/Groups?filter=members.value eq "2819c223-7f76-453a-919d-413861904646"
```

## Bulk Operations API

### Bulk User Creation

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:BulkRequest"],
  "Operations": [
    {
      "method": "POST",
      "path": "/Users",
      "bulkId": "qwerty",
      "data": {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "alice@acme.com",
        "name": {
          "givenName": "Alice",
          "familyName": "Smith"
        },
        "emails": [{"value": "alice@acme.com", "primary": true}],
        "active": true
      }
    }
  ]
}
```

## Webhook Events

### User Lifecycle Events

```json
{
  "eventType": "user.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "tenantId": "tenant-1",
  "resource": {
    "type": "User", 
    "id": "2819c223-7f76-453a-919d-413861904646"
  },
  "data": {
    // Full user object
  }
}
```

### Event Types

- `user.created` - New user provisioned
- `user.updated` - User attributes modified
- `user.activated` - User account activated
- `user.deactivated` - User account deactivated
- `user.deleted` - User permanently deleted
- `group.created` - New group created
- `group.updated` - Group modified
- `group.deleted` - Group deleted
- `membership.added` - User added to group
- `membership.removed` - User removed from group

## Development

### Local Setup

```bash
# Install dependencies
poetry install

# Start database
docker-compose up -d postgres redis

# Run migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn app.main:app --reload --port 8002
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration
```

## Security Considerations

- **Authentication**: All endpoints require valid bearer token or OAuth 2.0 authentication
- **Authorization**: Role-based access control with tenant isolation
- **Input Validation**: Comprehensive validation of all SCIM resources and operations
- **Rate Limiting**: Configurable rate limits to prevent abuse
- **Audit Logging**: Complete audit trail of all provisioning operations
- **Data Encryption**: All sensitive data encrypted at rest and in transit
- **Webhook Security**: Webhook payloads signed with HMAC for verification

## Monitoring and Observability

- **Health Checks**: Kubernetes-ready health and readiness probes
- **Metrics**: Prometheus metrics for performance and usage monitoring
- **Distributed Tracing**: OpenTelemetry integration for request tracing
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Error Tracking**: Comprehensive error reporting and alerting

## Compliance

- **SCIM 2.0 RFC 7643**: Full compliance with SCIM user and group schemas
- **SCIM 2.0 RFC 7644**: Complete implementation of SCIM protocol
- **SOC 2**: Audit logging and security controls for compliance
- **GDPR**: Data protection and right to be forgotten support
- **Enterprise Requirements**: Multi-tenancy, scalability, and reliability
