# Chat Service

Chat service with parental controls, moderation, and audit capabilities for the Aivo educational platform.

## Features

###  Parental Controls
- **AI Tutor Toggle**: Parents can enable/disable AI tutor access for learners
- **Time Limits**: Configurable time restrictions for AI tutor interactions
- **Content Filtering**: Multi-level content filtering (strict, moderate, relaxed)
- **Topic Controls**: Allow/block specific topics for conversations
- **Real-time Monitoring**: Live monitoring of all chat interactions
- **Daily Summaries**: Automated daily reports for parents

###  Content Moderation
- **Perspective API Integration**: Google Perspective API for toxicity detection
- **Soft/Hard Blocking**: Configurable blocking based on toxicity scores (>0.85 threshold)
- **PII Detection & Scrubbing**: Automatic detection and redaction of personal information
- **Human Review Queue**: Flagging of content requiring human review
- **Multi-level Filtering**: Adjustable moderation levels based on user preferences

###  Audit & Compliance
- **Merkle Chain**: Cryptographic audit trail for all messages
- **S3 Export**: Automated export to AWS S3 in JSON/Parquet formats
- **MongoDB Archiving**: Long-term storage in MongoDB for compliance
- **Data Retention**: Configurable retention policies
- **Export Tools**: Bulk export capabilities with PII filtering

###  Chat Types
- **Parent  Teacher**: Direct communication between parents and teachers
- **Parent  AI Coach**: Parents can consult with AI educational coaches
- **Learner  AI Tutor**: Students interact with AI tutors (with parental controls)
- **Teacher  AI Coach**: Teachers get pedagogical support from AI coaches

## Architecture

```
        
   FastAPI App         Moderation            Audit Chain   
                       Service                             
  Routes          Perspective     Merkle Tree   
  WebSockets          PII Detection       S3 Export     
  Auth                Content Filter      MongoDB       
        
                                                         
                                                         
        
   PostgreSQL           Perspective             AWS S3     
                           API                             
  Chat Sessions       Toxicity            Exports       
  Messages            Threats             Archives      
  Audit Logs          Profanity           Compliance    
        
```

## Installation

### Development Setup

1. **Clone and Navigate**
   ```bash
   cd services/chat-svc
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database Setup**
   ```bash
   # Start PostgreSQL (ensure it's running)
   alembic upgrade head
   ```

5. **Run the Service**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Docker Setup

1. **Build Image**
   ```bash
   docker build -t aivo-chat-svc .
   ```

2. **Run Container**
   ```bash
   docker run -p 8000:8000 --env-file .env aivo-chat-svc
   ```

## Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Perspective API (Required for moderation)
PERSPECTIVE_API_KEY=your_perspective_api_key

# AWS S3 (Required for exports)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name

# Anthropic Claude API (Required for AI features)
ANTHROPIC_API_KEY=your_anthropic_key
```

### Optional Environment Variables

```bash
# MongoDB (for archiving)
MONGODB_CONNECTION_STRING=mongodb://localhost:27017

# Redis (for caching)
REDIS_URL=redis://localhost:6379

# OpenAI (backup AI provider)
OPENAI_API_KEY=your_openai_key
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: [docs/api/rest/chat.yaml](../../docs/api/rest/chat.yaml)

## Key Endpoints

### Chat Sessions
- `POST /api/v1/chat/sessions` - Create chat session
- `GET /api/v1/chat/sessions` - List chat sessions
- `GET /api/v1/chat/sessions/{id}` - Get session details

### Messages
- `POST /api/v1/chat/messages` - Send message (auto-moderated)
- `GET /api/v1/chat/sessions/{id}/messages` - Get session messages

### Parental Controls
- `POST /api/v1/chat/parental-controls` - Create controls
- `GET /api/v1/chat/parental-controls/{parent_id}/{learner_id}` - Get controls
- `PUT /api/v1/chat/parental-controls/{id}` - Update controls

### Data Management
- `POST /api/v1/chat/export` - Export chat data
- `DELETE /api/v1/chat/messages` - Delete chat data

### Statistics & Audit
- `GET /api/v1/chat/stats/moderation` - Moderation statistics
- `GET /api/v1/chat/stats/sessions` - Session statistics
- `GET /api/v1/chat/audit/{message_id}` - Message audit trail

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_basic.py -v
```

## Deployment

### Production Checklist

1. **Environment Variables**
   - Set `ENVIRONMENT=production`
   - Configure all required API keys
   - Set up proper database connections

2. **Security**
   - Enable CORS restrictions
   - Configure allowed hosts
   - Set up JWT authentication

3. **Monitoring**
   - Health check endpoint: `/health`
   - Log aggregation configured
   - Metrics collection enabled

4. **Compliance**
   - S3 bucket configured for exports
   - MongoDB configured for archiving
   - Audit logging enabled

## Compliance Features

### COPPA Compliance
- Parental consent workflow
- Age verification integration
- Data minimization practices
- Configurable data retention

### FERPA Compliance
- Educational record protection
- Secure data transmission
- Audit trail maintenance
- Access control enforcement

### Data Protection
- PII detection and scrubbing
- Encryption at rest and in transit
- Right to deletion support
- Data export capabilities

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database URL format
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
   ```

2. **Perspective API Errors**
   ```bash
   # Verify API key and quota
   PERSPECTIVE_API_KEY=your_valid_key
   ```

3. **S3 Export Failures**
   ```bash
   # Check AWS credentials and bucket permissions
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   ```

### Logs

```bash
# View application logs
docker logs aivo-chat-svc

# Follow logs in real-time
docker logs -f aivo-chat-svc
```

## Development

### Code Structure

```
app/
 main.py              # FastAPI application
 models.py            # SQLAlchemy models
 schemas.py           # Pydantic schemas
 routes.py            # API routes
 database.py          # Database configuration
 moderation/          # Moderation service
    __init__.py      # Perspective API integration
 audit/               # Audit service
    __init__.py      # Merkle chain & export
 prompts/             # AI prompt templates
     ai_tutor_prompt.txt
     ai_coach_prompt.txt
```

### Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass
5. Run linting with `ruff`

## License

Internal use only - Aivo Educational Platform
