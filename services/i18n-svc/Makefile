.PHONY: help install dev test lint format extract-strings update-locales a11y-test clean
.DEFAULT_GOAL := help

help: ## Show this help message
@echo "Available commands:"
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
poetry install --with dev,accessibility

dev: ## Install development dependencies
poetry install --with dev,accessibility
poetry run pre-commit install

test: ## Run tests
poetry run pytest -v --cov=app --cov-report=html

lint: ## Run linting
poetry run ruff check app/
poetry run mypy app/
poetry run black --check app/

format: ## Format code
poetry run ruff format app/
poetry run black app/

extract-strings: ## Extract translatable strings
poetry run extract-strings

update-locales: ## Update locale files
poetry run update-locales

a11y-test: ## Run accessibility tests
poetry run validate-accessibility

clean: ## Clean up generated files
rm -rf .pytest_cache
rm -rf htmlcov
rm -rf .coverage
rm -rf dist
rm -rf build
find . -type d -name __pycache__ -delete
find . -type f -name "*.pyc" -delete

run-dev: ## Run development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
docker build -t i18n-svc .

docker-run: ## Run Docker container
docker run -p 8000:8000 i18n-svc
