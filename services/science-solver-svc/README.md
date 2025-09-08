# Science Solver Service

A FastAPI-based microservice for scientific problem solving, including unit
validation, chemical equation balancing, and diagram parsing.

## Features

- **Unit Validation**: Dimensional analysis and unit conversion
- **Chemical Equation Balancing**: Automatic balancing of chemical equations
- **Diagram Parsing**: Object detection and text extraction from scientific
  diagrams

## API Endpoints

### Health Check

- `GET /health` - Service health status

### Unit Validation

- `POST /units/validate` - Validate dimensional consistency of expressions
  with units

  ```json
  {
    "expression": "10 m/s + 5 ft/s",
    "target_system": "SI"
  }
  ```

### Chemical Equation Balancing

- `POST /chem/balance` - Balance chemical equations

  ```json
  {
    "equation": "H2 + O2 -> H2O",
    "balance_type": "standard"
  }
  ```

### Diagram Parsing

- `POST /diagram/parse` - Parse scientific diagrams for objects and text

  ```json
  {
    "image_data": "base64_encoded_image",
    "parse_type": "general",
    "confidence_threshold": 0.7
  }
  ```

## Dependencies

- FastAPI for the web framework
- OpenCV for image processing
- SymPy for symbolic mathematics
- NumPy/SciPy for scientific computing
- PIL/Pillow for image handling

## Development

### Setup

```bash
cd services/science-solver-svc
poetry install
```

### Running the Service

```bash
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
poetry run ruff check .
poetry run pylint app/
```

## Configuration

The service can be configured via environment variables or `.env` file:

- `SERVICE_NAME`: Service identifier (default: "science-solver-svc")
- `HOST`: Bind address (default: "127.0.0.1")
- `PORT`: Port number (default: 8000)
- `DEBUG`: Debug mode (default: False)
- `LOG_LEVEL`: Logging level (default: "INFO")
- `MAX_EQUATION_LENGTH`: Maximum equation length (default: 1000)
- `MAX_DIAGRAM_SIZE_MB`: Maximum diagram size in MB (default: 10)

## Architecture

The service follows a modular architecture:

- `app/main.py`: FastAPI application and endpoints
- `app/config.py`: Configuration management
- `app/schemas.py`: Pydantic models for request/response
- `tests/`: Test suite

## Docker

Build and run with Docker:

```bash
docker build -t science-solver-svc .
docker run -p 8000:8000 science-solver-svc
```
