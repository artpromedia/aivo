.PHONY: install test lint fmt clean run docker-build docker-run ci-validate

# Python environment
PYTHON := python3.11
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_BIN := $(VENV)/bin/python

# Install dependencies
install:
$(PYTHON) -m venv $(VENV)
$(PIP) install --upgrade pip
$(PIP) install poetry
poetry install

# Format code (Root-level lint hygiene)
fmt:
ruff format .
ruff check --fix .

# Lint code
lint:
ruff check .
mypy app/

# Run tests
test:
pytest tests/ -v --cov=app --cov-report=term-missing

# Run service locally
run:
poetry run start

# Run development server
dev:
poetry run dev

# Docker commands
docker-build:
docker build -t notification-service:latest .

docker-run:
docker run -p 8003:8003 --env-file .env notification-service:latest

# CI validation (lint hygiene check)
ci-validate: fmt
@if [ -n "$$(git diff --exit-code)" ]; then \
echo "Code formatting issues detected. Please run 'make fmt' locally."; \
git diff; \
exit 1; \
fi

# Pre-commit setup
setup-pre-commit:
poetry run pre-commit install

# Clean up
clean:
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf $(VENV)
rm -rf .pytest_cache
rm -rf .coverage
rm -rf htmlcov
rm -rf .mypy_cache

# Health check
health:
curl -f http://localhost:8003/health || exit 1

# Start all services for development
start-services:
docker-compose up -d redis
poetry run dev

# Stop all services
stop-services:
docker-compose down

# Show logs
logs:
docker-compose logs -f notification-service

# Deploy (placeholder)
deploy:
@echo "Deployment commands would go here"
