# Game Generation Service

A high-performance FastAPI service for generating accessible educational game
manifests with declarative content and sub-second latency.

## Features

### 🎮 Declarative Game Manifests

- **POST /manifest** - Generate complete game manifests from learner requirements
- Subject-specific game types (Math, English, Science, Art, Music)
- Grade-appropriate difficulty and interaction complexity
- Configurable duration (1-60 minutes)

### ♿ Accessibility First (A11y)

- **Reduced Motion** - Slower animations for motion sensitivity
- **High Contrast** - Enhanced visual contrast for low vision
- **Large Text** - Increased font sizes for readability
- **Audio Cues** - Audio narration and sound feedback
- **Simplified UI** - Reduced complexity for cognitive accessibility
- **Color Blind Friendly** - Alternative visual indicators

### ⚡ Performance Optimized

- **≤1s Latency Target** - Sub-second manifest generation
- **Template Caching** - Redis + in-memory cache layers
- **Cache Warming** - Pre-generation of common variants
- **Background Processing** - Non-blocking cache operations

### 📊 Monitoring & Analytics

- Real-time performance metrics
- Cache hit/miss statistics
- Generation time tracking
- Health check endpoints

## API Endpoints

### Core Endpoints

```bash
POST /manifest           - Generate game manifest
GET  /health            - Service health check
GET  /performance       - Performance statistics
```

### Cache Management

```bash
GET    /cache/stats     - Cache statistics
POST   /cache/warm      - Warm cache for subject/grade
DELETE /cache/clear     - Clear expired entries
```

### Discovery

```bash
GET /subjects/{subject}/games - Available games for subject/grade
```

## Request/Response Examples

### Generate Math Game Manifest

```json
POST /manifest
{
  "learner_id": "student-123",
  "subject": "math",
  "grade": 3,
  "duration_minutes": 15,
  "accessibility": {
    "reduced_motion": true,
    "high_contrast": false,
    "large_text": true,
    "audio_cues": true,
    "simplified_ui": false,
    "color_blind_friendly": false
  }
}
```

### Response

```json
{
  "manifest": {
    "learner_id": "student-123",
    "subject": "math",
    "grade": 3,
    "game_type": "puzzle",
    "difficulty": "medium",
    "duration_minutes": 15,
    "scenes": [
      {
        "scene_id": "scene_1",
        "title": "Math Puzzle 1",
        "instructions": "Solve the puzzle by arranging the numbers correctly.",
        "assets": [
          {
            "asset_id": "background",
            "asset_type": "image",
            "url": "https://cdn.example.com/game-assets/backgrounds/math_bg.jpg",
            "alt_text": "math themed background",
            "width": 1920,
            "height": 1080
          }
        ],
        "estimated_duration_seconds": 300,
        "required_interactions": 4
      }
    ],
    "scoring": {
      "points_per_correct": 20,
      "points_per_incorrect": -5,
      "time_bonus_enabled": false,
      "max_time_bonus": 10,
      "streak_multiplier_enabled": true,
      "max_streak_multiplier": 2.0
    },
    "accessibility": {
      "reduced_motion": true,
      "large_text": true,
      "audio_cues": true
    }
  },
  "generation_time_ms": 245,
  "cache_hit": false,
  "learner_id": "student-123"
}
```

## Configuration

### Environment Variables

```bash
GAME_GEN_HOST=0.0.0.0
GAME_GEN_PORT=8000
GAME_GEN_DEBUG=false

# Cache Configuration
GAME_GEN_CACHE_ENABLED=true
GAME_GEN_CACHE_REDIS_URL=redis://localhost:6379/0
GAME_GEN_CACHE_DEFAULT_TTL_SECONDS=3600

# Performance Targets
GAME_GEN_TARGET_GENERATION_TIME_MS=1000
GAME_GEN_MAX_CONCURRENT_GENERATIONS=50

# Assets
GAME_GEN_ASSETS_BASE_URL=https://cdn.example.com/game-assets
```

## Development

### Prerequisites

- Python 3.11+
- Redis (for caching)
- Docker (optional)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (if not using Docker)
redis-server

# Run the service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Docker

```bash
# Build image
docker build -t game-gen-svc .

# Run with Redis
docker-compose up
```

## Architecture

### Service Components

1. **FastAPI Application** - REST API with async endpoints
2. **Game Generation Service** - Core manifest generation logic
3. **Template Cache** - Multi-layer caching (Redis + in-memory)
4. **Accessibility Adapter** - A11y feature transformations

### Data Models

- **GameManifest** - Complete game definition
- **GameScene** - Individual game sections
- **GameAsset** - Media resources (images, audio, CSS)
- **AccessibilitySettings** - A11y configuration
- **ScoringConfig** - Points and feedback rules

### Performance Strategy

1. **Cache-First Architecture** - Check cache before generation
2. **Template Pre-warming** - Generate common variants ahead of time
3. **Async Processing** - Non-blocking operations
4. **Background Tasks** - Cache warming and cleanup
5. **Resource Optimization** - Efficient asset loading

## Game Types by Subject

### Mathematics

- **Puzzle** - Number arrangement and logic games
- **Quiz** - Mathematical problem solving
- **Sorting** - Number and pattern organization

### English Language Arts

- **Word Builder** - Letter and word construction
- **Matching** - Word-definition associations
- **Quiz** - Reading comprehension and vocabulary

### Science

- **Quiz** - Concept understanding and facts
- **Matching** - Scientific terms and definitions
- **Sorting** - Classification and categorization

### Art

- **Drawing** - Creative expression tools
- **Matching** - Color and style recognition
- **Memory** - Visual pattern recognition

### Music

- **Rhythm** - Timing and beat matching
- **Memory** - Musical pattern recognition
- **Matching** - Sound and instrument identification

## Accessibility Implementation

### Reduced Motion

- Slower animation timings
- Simplified transitions
- Extended interaction timeouts

### High Contrast

- Enhanced color differentiation
- Bold visual elements
- Alternative styling assets

### Large Text

- Increased font sizes
- Improved readability
- Reduced text density

### Audio Cues

- Voice narration for instructions
- Sound feedback for interactions
- Audio alternatives to visual elements

### Simplified UI

- Reduced visual complexity
- Clearer interaction areas
- Streamlined navigation

### Color Blind Friendly

- Pattern-based indicators
- Text labels for color coding
- High contrast combinations

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
```

### Performance Metrics

```bash
curl http://localhost:8000/performance
```

### Cache Statistics

```bash
curl http://localhost:8000/cache/stats
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Ensure accessibility compliance
5. Maintain performance targets (≤1s generation)

## License

See main repository LICENSE file.
