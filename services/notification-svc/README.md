# Notification Service

Real-time notification delivery system with WebSocket, Web Push, and SMS fallback.

## Features

- **WebSocket**: Real-time bidirectional communication
- **Web Push**: Browser push notifications (PWA support)
- **SMS**: Fallback for critical notifications
- **Message Queue**: Reliable delivery with retry logic
- **Templates**: Localized notification templates

## Architecture

```text
Client → WebSocket → Notification Service → Message Queue
                ↓                      ↓
           Web Push API            SMS Provider
```

## API Endpoints

- `WS /ws/notify` - WebSocket connection for real-time notifications
- `POST /push/subscribe` - Register push notification subscription
- `POST /notify` - Send notification via REST API

## Configuration

```yaml
WEBSOCKET_URL: ws://localhost:8000/ws/notify
PUSH_VAPID_PUBLIC_KEY: your-public-key
PUSH_VAPID_PRIVATE_KEY: your-private-key
SMS_PROVIDER: twilio
SMS_ACCOUNT_SID: your-sid
SMS_AUTH_TOKEN: your-token
```

## Development

1. Install dependencies: `pip install -r requirements-simple.txt`
2. Copy `.env.example` to `.env` and configure
3. Start Redis: `docker run -d -p 6379:6379 redis:latest`
4. Run service: `python dev_server.py`
