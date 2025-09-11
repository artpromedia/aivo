.PHONY: help install format lint type-check test py-fix run clean dev

help: ## Show this help message
@echo 'Usage: make [target]'
@echo ''
@echo 'Targets:'
@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
poetry install

format: ## Format code with black and isort
poetry run black .
poetry run isort .

lint: ## Lint code with flake8
poetry run flake8 .

type-check: ## Type check with mypy
poetry run mypy .

test: ## Run tests
poetry run pytest

py-fix: format lint type-check test ## Run all code quality checks (CI target)
@echo " All code quality checks passed!"

run: ## Run the application
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev: ## Start development environment
docker-compose up -d postgres redis
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker: ## Start Celery worker
poetry run celery -A app.tasks worker --loglevel=info

beat: ## Start Celery beat scheduler
poetry run celery -A app.tasks beat --loglevel=info

clean: ## Clean up build artifacts
find . -type d -name __pycache__ -delete
find . -type f -name "*.pyc" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +
rm -rf build dist .coverage htmlcov/ .pytest_cache/ .mypy_cache/

migrate: ## Run database migrations
poetry run alembic upgrade head

migration: ## Create new migration
poetry run alembic revision --autogenerate -m "$(MSG)"

docker-build: ## Build Docker image
docker build -t consent-ledger-svc .

docker-run: ## Run Docker container
docker run -p 8000:8000 consent-ledger-svc
