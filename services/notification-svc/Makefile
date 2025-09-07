.PHONY: install test lint fmt clean run docker-build docker-run

# Python environment
PYTHON := python3.11
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_BIN := $(VENV)/bin/python

# Install dependencies
install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

# Format code
fmt:
	$(VENV)/bin/ruff format .
	$(VENV)/bin/ruff check --fix .

# Lint code
lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/mypy services/

# Run tests
test:
	$(VENV)/bin/pytest tests/ -v --cov=services --cov-report=term-missing

# Run service locally
run:
	$(PYTHON_BIN) -m uvicorn services.notification_svc.app:app --reload --port 8000

# Docker commands
docker-build:
	docker build -t notification-service:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env notification-service:latest

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

# CI validation
ci-validate: fmt
	@if [ -n "$$(git diff --exit-code)" ]; then \
		echo "Code formatting issues detected. Please run 'make fmt' locally."; \
		git diff; \
		exit 1; \
	fi
