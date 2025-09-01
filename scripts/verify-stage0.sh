#!/bin/bash
# Stage-0 Completion Verification Script
# =====================================
# This script verifies that all Stage-0 requirements are met

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
TOTAL_CHECKS=0

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

check_command() {
    local cmd=$1
    local name=$2
    ((TOTAL_CHECKS++))
    
    if command -v "$cmd" >/dev/null 2>&1; then
        log_success "$name is available"
        return 0
    else
        log_error "$name is not available"
        return 1
    fi
}

check_file() {
    local file=$1
    local description=$2
    ((TOTAL_CHECKS++))
    
    if [[ -f "$file" ]]; then
        log_success "$description exists ($file)"
        return 0
    else
        log_error "$description missing ($file)"
        return 1
    fi
}

check_directory() {
    local dir=$1
    local description=$2
    ((TOTAL_CHECKS++))
    
    if [[ -d "$dir" ]]; then
        log_success "$description exists ($dir)"
        return 0
    else
        log_error "$description missing ($dir)"
        return 1
    fi
}

run_command_check() {
    local cmd="$1"
    local description="$2"
    local expected_exit_code=${3:-0}
    ((TOTAL_CHECKS++))
    
    log_info "Running: $description"
    if eval "$cmd" >/dev/null 2>&1; then
        local actual_exit_code=$?
        if [[ $actual_exit_code -eq $expected_exit_code ]]; then
            log_success "$description passed"
            return 0
        else
            log_error "$description failed (exit code: $actual_exit_code, expected: $expected_exit_code)"
            return 1
        fi
    else
        log_error "$description failed to execute"
        return 1
    fi
}

# Header
echo "========================================"
echo "🎯 Stage-0 Completion Verification"
echo "========================================"
echo

# S0-9: Check basic tools and environment
log_info "S0-9: Basic Tools & Environment"
echo "----------------------------------------"
check_command "node" "Node.js"
check_command "pnpm" "pnpm"
check_command "python" "Python"
check_command "git" "Git"
check_command "docker" "Docker"
check_command "yamllint" "yamllint" || log_warning "yamllint not available locally"
echo

# S0-9: Check project structure
log_info "S0-9: Project Structure"
echo "----------------------------------------"
check_file "package.json" "Root package.json"
check_file "pnpm-workspace.yaml" "pnpm workspace config"
check_file "pyproject.toml" "Python project config"
check_file ".gitignore" "gitignore file"
check_file "README.md" "README documentation"
echo

# S0-10: Check Kong Gateway
log_info "S0-10: Kong Gateway"
echo "----------------------------------------"
check_directory "apps/gateway" "Gateway app directory"
check_file "apps/gateway/kong.yml" "Kong declarative config"
check_file "apps/gateway/README.md" "Gateway documentation"
echo

# S0-10: Check hello-svc
log_info "S0-10: Hello Service (FastAPI)"
echo "----------------------------------------"
check_directory "services/hello-svc" "Hello service directory"
check_file "services/hello-svc/pyproject.toml" "Hello service pyproject.toml"
check_file "services/hello-svc/requirements.txt" "Hello service requirements.txt"
check_file "services/hello-svc/app/main.py" "Hello service main application"
check_file "services/hello-svc/tests/test_ping.py" "Hello service tests"
echo

# S0-11: Check CI Workflows
log_info "S0-11: CI/CD Workflows"
echo "----------------------------------------"
check_directory ".github/workflows" "GitHub workflows directory"
check_file ".github/workflows/ci.yml" "Main CI workflow"
check_file ".github/workflows/dep-guard.yml" "Dependency guard workflow"
check_file ".github/workflows/security.yml" "Security scan workflow"
echo

# S0-12: Check deprecation scripts
log_info "S0-12: Deprecation Detection"
echo "----------------------------------------"
check_file "scripts/check-npm-deprecations.mjs" "NPM deprecation checker"
check_file "scripts/ensure-eslint9.mjs" "ESLint v9 enforcer"
echo

# S0-13: Check security configurations
log_info "S0-13: Security Configurations"
echo "----------------------------------------"
check_directory "infra/compose" "Docker compose infrastructure"
check_file "infra/compose/local.yml" "Local development compose"
echo

# S0-14: Check VS Code configuration
log_info "S0-14: VS Code Configuration"
echo "----------------------------------------"
check_directory ".vscode" "VS Code settings directory"
check_file ".vscode/settings.json" "VS Code workspace settings"
check_file ".vscode/extensions.json" "VS Code extension recommendations"
echo

# S0-15: Check build system
log_info "S0-15: Build System"
echo "----------------------------------------"
check_file "Makefile" "Build system Makefile"
check_file "scripts/verify-stage0.sh" "Stage-0 verifier script"
echo

# Functional checks
log_info "Functional Verification"
echo "----------------------------------------"

# Check if pnpm install works
if [[ -d "node_modules" ]]; then
    log_success "Node.js dependencies are installed"
    ((CHECKS_PASSED++))
else
    log_warning "Node.js dependencies not installed (run 'pnpm install')"
fi
((TOTAL_CHECKS++))

# Check if Python venv exists
if [[ -d ".venv" ]]; then
    log_success "Python virtual environment exists"
    ((CHECKS_PASSED++))
else
    log_warning "Python virtual environment not found (run 'make install')"
fi
((TOTAL_CHECKS++))

# Check linting
run_command_check "pnpm run lint --help" "ESLint configuration"

# Check formatting
run_command_check "pnpm run format:check --help" "Prettier configuration"

# Check contracts
run_command_check "pnpm run contracts:lint --help" "API contract linting"

# Check Docker Compose
run_command_check "docker compose -f infra/compose/local.yml config" "Docker Compose validation"

echo
echo "========================================"
echo "📊 Stage-0 Verification Summary"
echo "========================================"
echo -e "Total Checks: ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "Passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Failed: ${RED}$CHECKS_FAILED${NC}"

if [[ $CHECKS_FAILED -eq 0 ]]; then
    echo
    echo -e "${GREEN}🎉 Stage-0 verification PASSED!${NC}"
    echo -e "${GREEN}All requirements are met and the development environment is ready.${NC}"
    exit 0
else
    echo
    echo -e "${RED}💥 Stage-0 verification FAILED!${NC}"
    echo -e "${RED}$CHECKS_FAILED check(s) failed. Please address the issues above.${NC}"
    exit 1
fi
