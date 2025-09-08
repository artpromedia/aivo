# Monorepo Makefile - Stage-0 Validation
# ==============================================

.PHONY: help install verify verify-all clean test lint format security deps-check

# Default target
help: ## Show this help message
	@echo "Monorepo Stage-0 Validation Commands"
	@echo "===================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation and setup
install: ## Install all dependencies (Node.js + Python)
	@echo "🔧 Installing Node.js dependencies..."
	corepack enable
	pnpm install
	@echo "🐍 Setting up Python environment..."
	python -m venv .venv
	.venv/Scripts/pip install -r services/hello-svc/requirements.txt
	@echo "✅ All dependencies installed"

# Core verification targets
verify: ## Run basic verification (lint + format check)
	@echo "🔍 Running basic verification..."
	pnpm run lint
	pnpm run format:check
	@echo "✅ Basic verification complete"

verify-all: ## Run complete Stage-0 verification
	@echo "🚀 Running complete Stage-0 verification..."
	@$(MAKE) lint
	@$(MAKE) format-check
	@$(MAKE) security
	@$(MAKE) deps-check
	@$(MAKE) contracts
	@$(MAKE) compose-check
	@$(MAKE) eslint9-check
	@echo "✅ All Stage-0 checks passed!"

# Individual check targets
lint: ## Run all linting (JS/TS, Python, YAML, Markdown, Docker)
	@echo "📝 Running linting checks..."
	pnpm run lint
	pnpm run lint:yml
	pnpm run lint:md
	pnpm run lint:docker

py-fix: ## Fix Python code formatting and linting issues
	@echo "🐍 Fixing Python code with Ruff..."
	ruff check --fix .
	ruff format .
	@echo "✅ Python code formatting complete"

format-check: ## Check code formatting
	@echo "🎨 Checking code formatting..."
	pnpm run format:check

security: ## Run security scans (Trivy + pip-audit)
	@echo "🔒 Running security scans..."
	@if command -v trivy >/dev/null 2>&1; then \
		echo "Running Trivy filesystem scan..."; \
		trivy fs --severity HIGH,CRITICAL --exit-code 1 .; \
	else \
		echo "⚠️  Trivy not installed locally - will run in CI"; \
	fi
	@echo "Running pip-audit for Python dependencies..."
	.venv/Scripts/python -m pip_audit -r services/hello-svc/requirements.txt --desc

deps-check: ## Check for deprecated npm packages
	@echo "📦 Checking for deprecated packages..."
	node scripts/check-npm-deprecations.mjs

contracts: ## Validate API contracts
	@echo "📋 Validating API contracts..."
	pnpm run contracts:lint

compose-check: ## Validate Docker Compose configuration
	@echo "🐳 Validating Docker Compose..."
	docker compose -f infra/compose/local.yml config >/dev/null

eslint9-check: ## Verify ESLint v9 usage
	@echo "🔧 Checking ESLint version..."
	node scripts/ensure-eslint9.mjs

# Testing targets
test: ## Run all tests
	@echo "🧪 Running tests..."
	@echo "Testing hello-svc..."
	cd services/hello-svc && ../../.venv/Scripts/python -m pytest tests/ -v

test-hello-svc: ## Run hello-svc tests specifically
	@echo "🧪 Testing hello-svc..."
	cd services/hello-svc && ../../.venv/Scripts/python -m pytest tests/ -v

# Development targets
format: ## Format all code
	@echo "🎨 Formatting code..."
	pnpm run format

clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning..."
	rm -rf node_modules
	rm -rf .venv
	rm -rf services/*/node_modules
	rm -rf services/*/__pycache__
	rm -rf services/*/tests/__pycache__
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

# Docker targets
compose-up: ## Start local development environment
	@echo "🐳 Starting development environment..."
	docker compose -f infra/compose/local.yml up -d

compose-down: ## Stop local development environment
	@echo "🐳 Stopping development environment..."
	docker compose -f infra/compose/local.yml down

compose-logs: ## Show Docker Compose logs
	docker compose -f infra/compose/local.yml logs -f

# Stage-0 completion verifier
stage0-verify: ## Comprehensive Stage-0 verification script
	@echo "🎯 Running Stage-0 Completion Verification..."
	@./scripts/verify-stage0.sh

# Stage-2 pipeline verifier
stage2-verify: ## Comprehensive Stage-2 pipeline verification
	@echo "🎯 Running Stage-2 Pipeline Verification..."
	@echo "Testing upload → ocr → topics → index → planner → game workflow..."
	tsx scripts/verify-stage2.ts

# Quick development workflow
dev-setup: install verify ## Complete development setup and verification
	@echo "🎉 Development environment ready!"

# CI simulation
ci-local: ## Simulate CI checks locally
	@echo "🔄 Simulating CI pipeline locally..."
	@$(MAKE) verify-all
	@$(MAKE) test
	@echo "✅ Local CI simulation complete!"
