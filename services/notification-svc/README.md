# Realtime Notification Service 

**#S2-10  Realtime Notifications (WS + Push + SMS fallback)  Realtime Engineer**

Advanced notification delivery system with WebSocket, Web Push, and SMS fallback specifically designed for IEP reminders and educational alerts.

##  Features

- ** Real-time WebSocket**: Bidirectional communication with JWT auth, heartbeat, and message replay
- ** Web Push Notifications**: Browser push for offline users with PWA support
- ** SMS Fallback**: Critical notifications via SMS when other channels fail
- ** IEP Reminder System**: Specialized templates for IEP meetings, deadlines, and compliance
- ** Localized Templates**: Multi-language support for diverse educational environments
- ** Analytics & Monitoring**: Comprehensive delivery tracking and performance metrics
- ** Security First**: JWT authentication, rate limiting, and audit logging

##  Architecture

```
Client Application
       
WebSocket Connection (JWT + Heartbeat + Replay-ID)
       
Notification Service
       

  Redis        Push API     SMS API    
  (Queue)      (Offline)    (Critical) 

```

### Real-time Message Flow

1. **WebSocket First**: Immediate delivery for online users
2. **Push Fallback**: Browser notifications for offline users  
3. **SMS Critical**: Emergency notifications for high-priority alerts
4. **Queue & Replay**: Message persistence with replay capability

##  Quick Start

### Prerequisites

- Python 3.11+
- Redis (for message queuing)
- Valid VAPID keys (for push notifications)
- Twilio account (for SMS)

### Installation

```bash
cd services/notification-svc
poetry install
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Configure required variables
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="your-secret-key"
export VAPID_PUBLIC_KEY="your-vapid-public-key"
export VAPID_PRIVATE_KEY="your-vapid-private-key"
export TWILIO_ACCOUNT_SID="your-twilio-sid"
export TWILIO_AUTH_TOKEN="your-twilio-token"
```

### Start Services

```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Start notification service
make run
# or for development
make dev
```

Service available at: http://localhost:8003

API Documentation: http://localhost:8003/docs

##  API Usage

### WebSocket Connection

```javascript
// Connect with JWT token and replay support
const ws = new WebSocket(
  'ws://localhost:8003/ws/notify?token=YOUR_JWT_TOKEN&replay_from=12345'
);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'iep_meeting_reminder':
      showIEPMeetingAlert(message.data);
      break;
    case 'iep_deadline_warning':
      showDeadlineWarning(message.data);
      break;
    case 'heartbeat':
      // Respond to heartbeat
      ws.send(JSON.stringify({type: 'pong'}));
      break;
  }
};
```

### Send IEP Meeting Reminder

```bash
curl -X POST "http://localhost:8003/notify" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "template_id": "iep_meeting_reminder",
    "notification_type": "iep_reminder",
    "channels": ["websocket", "push", "sms"],
    "priority": "high",
    "data": {
      "student_name": "Sarah Johnson",
      "meeting_date": "2025-09-15T14:00:00Z",
      "location": "Conference Room A",
      "attendees": ["Teacher", "Parent", "Counselor"],
      "iep_id": "iep_12345"
    },
    "locale": "en-US",
    "phone_number": "+1234567890"
  }'
```

**Response:**
```json
{
  "notification_id": "550e8400-e29b-41d4-a716-446655440000",
  "channels": {
    "websocket": "delivered",
    "push": "delivered", 
    "sms": "delivered"
  },
  "timestamp": "2025-09-11T10:00:00Z",
  "websocket_connections": 2,
  "replay_id": "12346",
  "estimated_delivery": "2025-09-11T10:00:00Z"
}
```

### Send IEP Deadline Warning

```bash
curl -X POST "http://localhost:8003/notify" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "template_id": "iep_deadline_warning",
    "notification_type": "deadline_warning",
    "channels": ["websocket", "push"],
    "priority": "critical",
    "data": {
      "student_name": "Michael Chen",
      "deadline_date": "2025-09-20T23:59:59Z",
      "days_remaining": 5,
      "action_required": "Submit IEP review documents",
      "iep_id": "iep_67890"
    },
    "locale": "en-US"
  }'
```

### Subscribe to Push Notifications

```javascript
// Register service worker and get subscription
const registration = await navigator.serviceWorker.register('/sw.js');
const subscription = await registration.pushManager.subscribe({
  userVisibleOnly: true,
  applicationServerKey: 'YOUR_VAPID_PUBLIC_KEY'
});

// Send subscription to server
await fetch('/push/subscribe', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  },
  body: JSON.stringify(subscription)
});
```

##  IEP Notification Types

### Available Templates

| Template ID | Description | Channels | Priority |
|-------------|-------------|----------|----------|
| `iep_meeting_reminder` | Upcoming IEP meeting notifications | WS, Push, SMS | High |
| `iep_deadline_warning` | IEP review deadline alerts | WS, Push, SMS | Critical |
| `iep_document_ready` | IEP documentation completion | WS, Push | Normal |
| `iep_parent_consent` | Parent consent requests | WS, Push, SMS | High |
| `iep_review_due` | Annual review reminders | WS, Push | Normal |
| `iep_progress_report` | Progress report notifications | WS, Push | Normal |

### Data Fields for IEP Notifications

```json
{
  "student_name": "Sarah Johnson",
  "student_id": "student_12345",
  "iep_id": "iep_67890",
  "meeting_date": "2025-09-15T14:00:00Z",
  "deadline_date": "2025-09-20T23:59:59Z",
  "location": "Conference Room A",
  "attendees": ["Teacher", "Parent", "Counselor"],
  "case_manager": "Ms. Smith",
  "action_required": "Submit review documents",
  "days_remaining": 5,
  "meeting_type": "Annual Review",
  "compliance_status": "On Track"
}
```

##  WebSocket Features

### Heartbeat Mechanism

- **Automatic**: Server sends ping every 30 seconds
- **Client Response**: Send `{type: 'pong'}` to maintain connection
- **Timeout**: Connection closed after 90 seconds without response

### Message Replay System

- **Replay ID**: Each message has a sequential replay ID
- **Recovery**: Connect with `replay_from` parameter to get missed messages
- **History**: Last 100 messages per user stored for replay

### Connection Management

```javascript
class NotificationClient {
  constructor(token, replayFrom = null) {
    this.token = token;
    this.replayFrom = replayFrom;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    const url = `ws://localhost:8003/ws/notify?token=${this.token}${
      this.replayFrom ? `&replay_from=${this.replayFrom}` : ''
    }`;
    
    this.ws = new WebSocket(url);
    this.ws.onmessage = this.handleMessage.bind(this);
    this.ws.onclose = this.handleDisconnect.bind(this);
  }

  handleMessage(event) {
    const message = JSON.parse(event.data);
    
    // Store replay ID for reconnection
    if (message.replay_id) {
      this.lastReplayId = message.replay_id;
    }
    
    // Handle different message types
    switch (message.type) {
      case 'heartbeat':
        this.ws.send(JSON.stringify({type: 'pong'}));
        break;
      case 'iep_meeting_reminder':
        this.showIEPReminder(message);
        break;
      // ... other message types
    }
  }

  handleDisconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.replayFrom = this.lastReplayId;
        this.connect();
        this.reconnectAttempts++;
      }, 1000 * Math.pow(2, this.reconnectAttempts));
    }
  }
}
```

##  Analytics & Monitoring

### Health Check

```bash
curl http://localhost:8003/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-11T10:00:00Z",
  "version": "1.0.0",
  "total_connections": 150,
  "active_users": 75,
  "average_duration_seconds": 1200,
  "replay_sequence": 12346,
  "redis": "healthy",
  "services": {
    "websocket": "healthy",
    "push": "healthy", 
    "sms": "healthy",
    "templates": "healthy"
  }
}
```

### Get Analytics

```bash
curl "http://localhost:8003/analytics?start_date=2025-09-01&end_date=2025-09-11" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "total_notifications": 15420,
  "delivery_stats": {
    "websocket": {
      "sent": 15420,
      "delivered": 12800,
      "failed": 120,
      "success_rate": 0.83
    },
    "push": {
      "sent": 8500,
      "delivered": 8100,
      "failed": 400,
      "success_rate": 0.95
    },
    "sms": {
      "sent": 450,
      "delivered": 440,
      "failed": 10,
      "success_rate": 0.98
    }
  },
  "notification_types": {
    "iep_reminder": 5200,
    "meeting_alert": 3800,
    "deadline_warning": 2100
  },
  "response_times": {
    "average_ms": 245,
    "p95_ms": 850,
    "p99_ms": 1200
  },
  "connection_stats": {
    "total_connections": 150,
    "active_users": 75
  }
}
```

##  Development

### Code Quality (Ruff Lint Hygiene)

```bash
# Format code (root-level)
make fmt

# Check formatting for CI
make ci-validate

# Full lint check  
make lint

# Type checking
mypy app/
```

### Testing

```bash
# Run all tests
make test

# Run specific test category
pytest tests/test_websocket.py -v
pytest tests/test_iep_notifications.py -v

# Test with coverage
pytest --cov=app --cov-report=html
```

### Local Development

```bash
# Start all development services
make start-services

# View logs
make logs

# Health check
make health

# Stop all services
make stop-services
```

##  Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY . .
EXPOSE 8003

CMD ["poetry", "run", "start"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  notification-service:
    build: .
    ports:
      - "8003:8003"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - VAPID_PUBLIC_KEY=${VAPID_PUBLIC_KEY}
      - VAPID_PRIVATE_KEY=${VAPID_PRIVATE_KEY}
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: notification-service
  template:
    metadata:
      labels:
        app: notification-service
    spec:
      containers:
      - name: notification-service
        image: notification-service:latest
        ports:
        - containerPort: 8003
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        livenessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 30
          periodSeconds: 10
```

##  Security & Compliance

### Authentication
- **JWT Tokens**: Required for all WebSocket and REST endpoints
- **Token Validation**: Automatic token verification with user context
- **Scope-based Access**: Fine-grained permissions for different notification types

### Privacy & Data Protection
- **FERPA Compliance**: Educational records protection
- **COPPA Compliance**: Child privacy protection
- **Data Minimization**: Only required data stored and transmitted
- **Encryption**: All data encrypted in transit and at rest

### Audit & Monitoring
- **Complete Audit Trail**: All notifications logged with timestamps
- **User Activity Tracking**: Connection and interaction monitoring  
- **Compliance Reporting**: Automated compliance status reports
- **Security Alerts**: Real-time security event notifications

##  Error Handling

### Common Error Codes

| Code | Error | Description | Resolution |
|------|-------|-------------|------------|
| 401 | Unauthorized | Invalid JWT token | Refresh authentication token |
| 403 | Forbidden | Insufficient permissions | Check user roles and permissions |
| 429 | Rate Limited | Too many requests | Implement exponential backoff |
| 500 | Server Error | Internal service failure | Check service health and logs |

### WebSocket Error Handling

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
  // Implement reconnection logic
};

ws.onclose = (event) => {
  if (event.code === 1008) {
    // Unauthorized - refresh token
    refreshAuthToken().then(() => reconnect());
  } else if (event.code === 1011) {
    // Server error - retry with backoff
    scheduleReconnect();
  }
};
```

##  Performance & Scaling

### Optimization Features
- **Connection Pooling**: Efficient Redis connection management
- **Message Batching**: Bulk operations for high throughput
- **Caching**: Template and user preference caching
- **Rate Limiting**: Per-user and per-service rate limits

### Scaling Considerations
- **Horizontal Scaling**: Multiple service instances with Redis clustering
- **Load Balancing**: WebSocket sticky sessions for connection management
- **Database Scaling**: Read replicas for analytics queries
- **CDN Integration**: Static asset delivery for push notification icons

##  Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/enhanced-iep-reminders`
3. Follow lint hygiene: `make fmt && make ci-validate`
4. Add comprehensive tests
5. Update documentation
6. Submit pull request

### Code Style Guidelines

- **Line Length**: 100 characters maximum
- **Type Hints**: Required for all functions and methods
- **Docstrings**: Google style for all public APIs
- **Error Handling**: Specific exceptions with detailed messages
- **Logging**: Structured logging with contextual information

##  License

MIT License - See LICENSE file for details.

---

**feat(notification): websocket+push + sms fallback for iep reminders** 

*Real-time educational notifications that keep students, parents, and educators connected.*
