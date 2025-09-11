.PHONY: help install dev-install lint format type-check test py-fix clean run

# Default target
help:
@echo "Available commands:"
@echo "  install     - Install production dependencies"
@echo "  dev-install - Install development dependencies"
@echo "  lint        - Run linting (flake8)"
@echo "  format      - Format code (black, isort)"
@echo "  type-check  - Run type checking (mypy)"
@echo "  test        - Run tests"
@echo "  py-fix      - Run all code quality checks and fixes"
@echo "  clean       - Clean temporary files"
@echo "  run         - Run the application"

install:
poetry install --only=main

dev-install:
poetry install

lint:
poetry run flake8 app/ config/ --max-line-length=88 --extend-ignore=E203,W503

format:
poetry run black app/ config/
poetry run isort app/ config/

type-check:
poetry run mypy app/ config/

test:
poetry run pytest

# Comprehensive code quality target for CI/CD
py-fix: format lint type-check test
@echo " All code quality checks passed!"

clean:
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +
rm -rf .pytest_cache/
rm -rf .mypy_cache/
rm -rf dist/
rm -rf build/

run:
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
