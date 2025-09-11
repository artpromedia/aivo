.PHONY: install dev test lint format py-fix clean build run docker-build docker-run

# Python environment and dependencies
install:
poetry install

dev:
poetry install --with dev

# Code quality and testing
test:
poetry run pytest

lint:
poetry run ruff check app/
poetry run mypy app/

format:
poetry run black app/
poetry run ruff format app/

py-fix: format
poetry run ruff check --fix app/

# Development server
run:
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Celery workers
worker:
poetry run celery -A app.jobs.celery_app worker --loglevel=info

beat:
poetry run celery -A app.jobs.celery_app beat --loglevel=info

# Docker
docker-build:
docker build -t roster-sync-service .

docker-run:
docker run -p 8001:8001 roster-sync-service

# Cleanup
clean:
find . -type d -name __pycache__ -delete
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type f -name ".coverage" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +

# Database migrations
db-upgrade:
poetry run alembic upgrade head

db-downgrade:
poetry run alembic downgrade -1

db-migration:
poetry run alembic revision --autogenerate -m "$(MESSAGE)"

# Pre-commit hooks
pre-commit-install:
poetry run pre-commit install

pre-commit-run:
poetry run pre-commit run --all-files
