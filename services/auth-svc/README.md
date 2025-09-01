# Auth Service

FastAPI-based authentication and authorization service with JWT tokens and role-based access control.

## Features

- **Guardian Registration**: Self-service registration for guardian users
- **JWT Authentication**: Secure token-based authentication with refresh token rotation
- **Role-Based Access Control (RBAC)**: Support for guardian, teacher, staff, and admin roles
- **Teacher Invitations**: Staff can invite teachers to join their tenant
- **Multi-Tenancy**: Support for multiple organizations/schools
- **Password Security**: Argon2 password hashing
- **Async Support**: Built with FastAPI and SQLAlchemy async for high performance

## API Endpoints

### Authentication

- `POST /api/v1/auth/register-guardian` - Register a new guardian
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/login-staff` - Staff login with optional tenant context
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout and revoke refresh token

### User Management

- `POST /api/v1/auth/invite-teacher` - Invite a teacher (staff/admin only)
- `POST /api/v1/auth/accept-invite` - Accept teacher/staff invitation
- `GET /api/v1/auth/me` - Get current user profile

### Health

- `GET /health` - Health check endpoint
- `GET /` - Service information

## User Roles

- **Guardian**: Parents/guardians who can register themselves
- **Teacher**: Invited by staff, associated with a specific tenant
- **Staff**: Organization employees, can invite teachers
- **Admin**: System administrators with full access

## JWT Token Claims

```json
{
  "sub": "user-id",
  "email": "user@example.com", 
  "role": "guardian|teacher|staff|admin",
  "tenant_id": "tenant-uuid",
  "dash_context": "guardian_dash|teacher_dash|staff_dash|admin_dash",
  "exp": 1234567890,
  "iat": 1234567890
}
```

## Development Setup

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run database migrations**:

   ```bash
   alembic upgrade head
   ```

4. **Start the server**:

   ```bash
   uvicorn app.main:app --reload
   ```

5. **Run tests**:

   ```bash
   pytest
   ```

## Database Schema

### Users Table

- `id` (UUID, Primary Key)
- `email` (String, Unique)
- `hashed_password` (String)
- `first_name`, `last_name` (String)
- `phone` (String, Optional)
- `role` (Enum: guardian, teacher, staff, admin)
- `tenant_id` (UUID, Optional - for multi-tenancy)
- `status` (Enum: active, inactive, suspended)
- `is_email_verified` (Boolean)
- `created_at`, `updated_at`, `last_login_at` (DateTime)

### Refresh Tokens Table

- `id` (UUID, Primary Key)
- `token` (String, Unique)
- `user_id` (UUID, Foreign Key)
- `expires_at` (DateTime)
- `is_revoked` (Boolean)
- `user_agent`, `ip_address` (String, Optional)
- `created_at` (DateTime)

### Invite Tokens Table

- `id` (UUID, Primary Key)
- `token` (String, Unique)
- `email` (String)
- `role` (Enum: teacher, staff)
- `tenant_id` (UUID)
- `invited_by` (UUID, Foreign Key)
- `expires_at` (DateTime)
- `is_used` (Boolean)
- `used_at` (DateTime, Optional)
- `created_at` (DateTime)

## Security Features

- **Password Hashing**: Argon2 with configurable parameters
- **JWT Security**: Asymmetric encryption support (RS256) for production
- **Token Rotation**: Refresh tokens are rotated on each use
- **CORS Protection**: Configurable allowed origins
- **Rate Limiting**: Ready for rate limiting middleware
- **Input Validation**: Pydantic schemas for all requests

## Production Considerations

1. **Use RSA Keys for JWT**: Generate RSA key pair for RS256 algorithm
2. **Database Connection Pooling**: Configure appropriate pool sizes
3. **Environment Variables**: Set all sensitive configuration via environment
4. **Monitoring**: Add logging and metrics collection
5. **Rate Limiting**: Implement rate limiting for auth endpoints
6. **Email Service**: Integrate with notification service for invite emails

## Docker Deployment

```bash
# Build image
docker build -t auth-svc .

# Run container
docker run -p 8000:8000 --env-file .env auth-svc
```

## Testing

The service includes comprehensive tests covering:

- User registration and login flows
- JWT token generation and validation
- Refresh token rotation
- Teacher invitation workflow
- Role-based access control
- Error handling and edge cases

Run tests with:

```bash
pytest -v
```
