.PHONY: help install dev-install test lint format type-check py-fix clean docker-build docker-run

help: ## Show this help message
@echo "Available commands:"
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
poetry install --only main

dev-install: ## Install all dependencies including dev
poetry install

test: ## Run tests
poetry run pytest tests/ -v

lint: ## Run linting checks
poetry run ruff check app/ tests/
poetry run mypy app/

format: ## Format code
poetry run black app/ tests/
poetry run ruff format app/ tests/

type-check: ## Run type checking
poetry run mypy app/

py-fix: ## Fix and format Python code (for CI)
poetry run ruff check --fix app/ tests/
poetry run ruff format app/ tests/
poetry run black app/ tests/

clean: ## Clean up build artifacts
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +
rm -rf dist/ build/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/

docker-build: ## Build Docker image
docker build -t media-svc:latest .

docker-run: ## Run Docker container
docker-compose up -d

docker-stop: ## Stop Docker containers
docker-compose down

docker-logs: ## Show Docker logs
docker-compose logs -f

celery-worker: ## Start Celery worker
poetry run celery -A app.workers.celery_app worker --loglevel=info

celery-beat: ## Start Celery beat scheduler
poetry run celery -A app.workers.celery_app beat --loglevel=info

celery-flower: ## Start Celery Flower monitoring
poetry run celery -A app.workers.celery_app flower

dev-server: ## Start development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

init-db: ## Initialize database
poetry run alembic upgrade head

migration: ## Create new migration
poetry run alembic revision --autogenerate -m "$(msg)"

upgrade-db: ## Upgrade database to latest migration
poetry run alembic upgrade head

downgrade-db: ## Downgrade database by one migration
poetry run alembic downgrade -1
