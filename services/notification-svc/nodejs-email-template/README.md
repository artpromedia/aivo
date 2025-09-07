# Node.js Email Service

A production-ready Node.js email service that supports multiple email providers
(SendGrid, AWS SES, SMTP).

## Features

- ✅ Multi-provider support (SendGrid, AWS SES, SMTP)
- ✅ Auto-fallback between providers
- ✅ Health checks and monitoring
- ✅ Security hardened with Helmet
- ✅ Structured logging with Winston
- ✅ Docker ready with security best practices
- ✅ Non-root user execution
- ✅ Graceful shutdown handling

## Quick Start

### Development Setup

This project uses **pnpm** as the package manager and **ESLint 9** with flat
config.

1. **Install dependencies:**

```bash
pnpm install
```

1. **Run linting:**

```bash
pnpm run lint
pnpm run lint:fix  # Auto-fix issues
```

1. **Start development server:**

```bash
pnpm run dev
```

### Using Docker (Recommended)

1. **Build the image:**

```bash
docker build -f ../Dockerfile.email-nodejs -t aivo-email-service .
```

1. **Run with environment variables:**

```bash
docker run -d \
  --name email-service \
  -p 8080:8080 \
  -e SENDGRID_API_KEY=your_key_here \
  -e FROM_EMAIL=noreply@yourdomain.com \
  aivo-email-service
```

### Local Development

1. **Install dependencies:**

```bash
npm install
```

1. **Copy environment file:**

```bash
cp .env.example .env
# Edit .env with your provider credentials
```

1. **Start development server:**

```bash
npm run dev
```

## API Endpoints

### Health Check

```http
GET /health
```

### Detailed Health Check

```http
GET /health/detailed
```

### Send Email

```http
POST /api/email/send
Content-Type: application/json

{
  "to": "user@example.com",
  "subject": "Test Email",
  "text": "Hello from AIVO!",
  "html": "<h1>Hello from AIVO!</h1>",
  "provider": "auto"  // Optional: "sendgrid", "ses", "smtp", or "auto"
}
```

## Configuration

### Environment Variables

| Variable                | Description                          | Required |
| ----------------------- | ------------------------------------ | -------- |
| `PORT`                  | Server port (default: 8080)          | No       |
| `NODE_ENV`              | Environment (development/production) | No       |
| `FROM_EMAIL`            | Default sender email                 | Yes      |
| `SENDGRID_API_KEY`      | SendGrid API key                     | Optional |
| `AWS_ACCESS_KEY_ID`     | AWS access key                       | Optional |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key                       | Optional |
| `AWS_REGION`            | AWS region (default: us-east-1)      | Optional |
| `SMTP_HOST`             | SMTP server host                     | Optional |
| `SMTP_PORT`             | SMTP server port (default: 587)      | Optional |
| `SMTP_USER`             | SMTP username                        | Optional |
| `SMTP_PASS`             | SMTP password                        | Optional |

### Provider Priority

When using `"provider": "auto"`, the service will attempt providers in this
order:

1. SendGrid (if `SENDGRID_API_KEY` is set)
1. AWS SES (if AWS credentials are set)
1. SMTP (if SMTP config is set)

## Docker Security Features

- ✅ Multi-stage build for smaller images
- ✅ Alpine Linux with security updates
- ✅ Non-root user (mailuser:1001)
- ✅ dumb-init for proper signal handling
- ✅ Minimal attack surface

## Monitoring

### Health Endpoints

- **Basic health:** `GET /health` - Returns service status
- **Detailed health:** `GET /health/detailed` - Returns detailed info including
  provider configuration

### Logging

All requests and errors are logged with structured JSON format using Winston.

## Integration with AIVO

This service can replace or complement the Python `email_service.py` in the
notification service. To integrate:

1. **Update notification service** to call this HTTP API instead of direct
   email sending
1. **Add to Kong Gateway** for routing and load balancing
1. **Configure in Docker Compose** for orchestrated deployment

Example integration from Python:

```python
import requests

async def send_email(to: str, subject: str, html: str):
    response = requests.post(
        'http://email-service:8080/api/email/send',
        json={
            'to': to,
            'subject': subject,
            'html': html
        }
    )
    return response.json()
```
