# Math Recognizer Service

Convert digital ink to LaTeX/AST and grade mathematical expressions using
Computer Algebra Systems (CAS).

## Features

- **Ink Recognition**: Convert digital ink strokes to mathematical expressions
- **LaTeX Generation**: Output clean LaTeX for mathematical expressions
- **AST Conversion**: Generate Abstract Syntax Trees for programmatic processing
- **Mathematical Grading**: Grade expressions for correctness and equivalence
  using SymPy
- **Session Support**: Process ink from session IDs or direct ink data
- **CAS Integration**: Comprehensive Computer Algebra System capabilities

## API Endpoints

### Recognition

#### `POST /recognize/{session_id}`

Recognize mathematical expression from an ink session.

**Parameters:**

- `session_id`: UUID of the ink session
- `page_number`: Page number to recognize (default: 1)
- `region_x`, `region_y`, `region_width`, `region_height`: Optional bounding box

**Response:**

```json
{
  "latex": "x^2 + 2x + 1",
  "ast": {...},
  "confidence": 0.95,
  "success": true
}
```

#### `POST /recognize`

Recognize mathematical expression from direct ink data.

**Request:**

```json
{
  "strokes": [
    {
      "points": [
        {"x": 0.0, "y": 0.0, "pressure": 1.0, "timestamp": 0}
      ]
    }
  ],
  "width": 100.0,
  "height": 50.0
}
```

### Grading

#### `POST /grade`

Grade mathematical expressions for correctness and equivalence.

**Request:**

```json
{
  "student_expression": "x^2",
  "correct_expression": "x**2",
  "expression_type": "algebraic",
  "check_equivalence": true,
  "show_steps": true
}
```

**Response:**

```json
{
  "is_correct": true,
  "score": 1.0,
  "feedback": "Correct!",
  "is_equivalent": true,
  "steps": [...]
}
```

### Health

#### `GET /health`

Service health check.

#### `GET /`

Service information.

## Configuration

Environment variables:

- `HOST`: Service host (default: "127.0.0.1")
- `PORT`: Service port (default: 8000)
- `LOG_LEVEL`: Logging level (default: "info")
- `DEBUG`: Debug mode (default: false)
- `RECOGNITION_CONFIDENCE_THRESHOLD`: Min confidence for recognition (default: 0.7)
- `RECOGNITION_TIMEOUT_SECONDS`: Recognition timeout (default: 30)
- `CAS_PROVIDER`: CAS provider (default: "sympy")
- `INK_SERVICE_URL`: External ink service URL

## Development

### Setup

```bash
# Install dependencies
poetry install

# Run the service
poetry run uvicorn app.main:app --reload --port 8000

# Run tests
poetry run pytest

# Check linting
poetry run ruff check .
poetry run ruff format .
```

### Architecture

- **recognition_service.py**: Main recognition logic and ML integration
- **cas_service.py**: Computer Algebra System operations using SymPy
- **schemas.py**: Pydantic models for API validation
- **config.py**: Configuration management
- **main.py**: FastAPI application and endpoints

### ML Integration

The service includes placeholder ML recognition methods that can be replaced with:

- TensorFlow/PyTorch models
- Cloud-based recognition APIs
- Custom neural networks

### CAS Features

- Expression parsing and simplification
- LaTeX conversion and AST generation
- Mathematical equivalence checking
- Step-by-step equation solving
- Symbolic computation

## Docker

```bash
# Build image
docker build -t math-recognizer-svc .

# Run container
docker run -p 8000:8000 math-recognizer-svc
```

## Dependencies

- **FastAPI**: Web framework
- **SymPy**: Computer Algebra System
- **Pillow**: Image processing
- **NumPy**: Numerical computing
- **HTTPX**: Async HTTP client
- **Pydantic**: Data validation

## License

See LICENSE file in the monorepo root.
