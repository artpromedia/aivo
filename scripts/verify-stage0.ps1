# Stage-0 Completion Verification Script (PowerShell)
# ===================================================
# This script verifies that all Stage-0 requirements are met

$ErrorActionPreference = "Continue"

# Counters
$script:ChecksPassed = 0
$script:ChecksFailed = 0
$script:TotalChecks = 0

# Helper functions
function Write-Info {
    param($message)
    Write-Host "ℹ️  $message" -ForegroundColor Blue
}

function Write-Success {
    param($message)
    Write-Host "✅ $message" -ForegroundColor Green
    $script:ChecksPassed++
}

function Write-Warning {
    param($message)
    Write-Host "⚠️  $message" -ForegroundColor Yellow
}

function Write-Error {
    param($message)
    Write-Host "❌ $message" -ForegroundColor Red
    $script:ChecksFailed++
}

function Test-Command {
    param($command, $name)
    $script:TotalChecks++
    
    try {
        $null = Get-Command $command -ErrorAction Stop
        Write-Success "$name is available"
        return $true
    }
    catch {
        Write-Error "$name is not available"
        return $false
    }
}

function Test-FileExists {
    param($path, $description)
    $script:TotalChecks++
    
    if (Test-Path $path -PathType Leaf) {
        Write-Success "$description exists ($path)"
        return $true
    }
    else {
        Write-Error "$description missing ($path)"
        return $false
    }
}

function Test-DirectoryExists {
    param($path, $description)
    $script:TotalChecks++
    
    if (Test-Path $path -PathType Container) {
        Write-Success "$description exists ($path)"
        return $true
    }
    else {
        Write-Error "$description missing ($path)"
        return $false
    }
}

function Test-CommandExecution {
    param($command, $description)
    $script:TotalChecks++

    Write-Info "Running: $description"
    try {
        $null = Invoke-Expression $command 2>&1
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0 -or $null -eq $exitCode) {
            Write-Success "$description passed"
            return $true
        }
        else {
            Write-Error "$description failed (exit code: $exitCode)"
            return $false
        }
    }
    catch {
        Write-Error "$description failed to execute: $($_.Exception.Message)"
        return $false
    }
}

# Header
Write-Host "========================================"
Write-Host "🎯 Stage-0 Completion Verification" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host ""

# S0-9: Check basic tools and environment
Write-Info "S0-9: Basic Tools and Environment"
Write-Host "----------------------------------------"
Test-Command "node" "Node.js"
Test-Command "pnpm" "pnpm"
Test-Command "python" "Python"
Test-Command "git" "Git"
Test-Command "docker" "Docker"
if (-not (Test-Command "yamllint" "yamllint")) {
    Write-Warning "yamllint not available locally"
}
Write-Host ""

# S0-9: Check project structure
Write-Info "S0-9: Project Structure"
Write-Host "----------------------------------------"
Test-FileExists "package.json" "Root package.json"
Test-FileExists "pnpm-workspace.yaml" "pnpm workspace config"
Test-FileExists "pyproject.toml" "Python project config"
Test-FileExists ".gitignore" "gitignore file"
Test-FileExists "README.md" "README documentation"
Write-Host ""

# S0-10: Check Kong Gateway
Write-Info "S0-10: Kong Gateway"
Write-Host "----------------------------------------"
Test-DirectoryExists "apps/gateway" "Gateway app directory"
Test-FileExists "apps/gateway/kong.yml" "Kong declarative config"
Test-FileExists "apps/gateway/README.md" "Gateway documentation"
Write-Host ""

# S0-10: Check hello-svc
Write-Info "S0-10: Hello Service (FastAPI)"
Write-Host "----------------------------------------"
Test-DirectoryExists "services/hello-svc" "Hello service directory"
Test-FileExists "services/hello-svc/pyproject.toml" "Hello service pyproject.toml"
Test-FileExists "services/hello-svc/requirements.txt" "Hello service requirements.txt"
Test-FileExists "services/hello-svc/app/main.py" "Hello service main application"
Test-FileExists "services/hello-svc/tests/test_ping.py" "Hello service tests"
Write-Host ""

# S0-11: Check CI Workflows
Write-Info "S0-11: CI/CD Workflows"
Write-Host "----------------------------------------"
Test-DirectoryExists ".github/workflows" "GitHub workflows directory"
Test-FileExists ".github/workflows/ci.yml" "Main CI workflow"
Test-FileExists ".github/workflows/dep-guard.yml" "Dependency guard workflow"
Test-FileExists ".github/workflows/security.yml" "Security scan workflow"
Write-Host ""

# S0-12: Check deprecation scripts
Write-Info "S0-12: Deprecation Detection"
Write-Host "----------------------------------------"
Test-FileExists "scripts/check-npm-deprecations.mjs" "NPM deprecation checker"
Test-FileExists "scripts/ensure-eslint9.mjs" "ESLint v9 enforcer"
Write-Host ""

# S0-13: Check security configurations
Write-Info "S0-13: Security Configurations"
Write-Host "----------------------------------------"
Test-DirectoryExists "infra/compose" "Docker compose infrastructure"
Test-FileExists "infra/compose/local.yml" "Local development compose"
Write-Host ""

# S0-14: Check VS Code configuration
Write-Info "S0-14: VS Code Configuration"
Write-Host "----------------------------------------"
Test-DirectoryExists ".vscode" "VS Code settings directory"
Test-FileExists ".vscode/settings.json" "VS Code workspace settings"
Test-FileExists ".vscode/extensions.json" "VS Code extension recommendations"
Write-Host ""

# S0-15: Check build system
Write-Info "S0-15: Build System"
Write-Host "----------------------------------------"
Test-FileExists "Makefile" "Build system Makefile"
Test-FileExists "scripts/verify-stage0.sh" "Stage-0 verifier script (bash)"
Test-FileExists "scripts/verify-stage0.ps1" "Stage-0 verifier script (PowerShell)"
Write-Host ""

# Functional checks
Write-Info "Functional Verification"
Write-Host "----------------------------------------"

# Check if pnpm install works
$script:TotalChecks++
if (Test-Path "node_modules") {
    Write-Success "Node.js dependencies are installed"
    $script:ChecksPassed++
}
else {
    Write-Warning "Node.js dependencies not installed (run 'pnpm install')"
}

# Check if Python venv exists
$script:TotalChecks++
if (Test-Path ".venv") {
    Write-Success "Python virtual environment exists"
    $script:ChecksPassed++
}
else {
    Write-Warning "Python virtual environment not found (run 'make install')"
}

# Check Docker Compose
Test-CommandExecution "docker compose -f infra/compose/local.yml config" "Docker Compose validation"

Write-Host ""
Write-Host "========================================"
Write-Host "📊 Stage-0 Verification Summary" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host "Total Checks: $($script:TotalChecks)" -ForegroundColor Blue
Write-Host "Passed: $($script:ChecksPassed)" -ForegroundColor Green
Write-Host "Failed: $($script:ChecksFailed)" -ForegroundColor Red

if ($script:ChecksFailed -eq 0) {
    Write-Host ""
    Write-Host "🎉 Stage-0 verification PASSED!" -ForegroundColor Green
    Write-Host "All requirements are met and the development environment is ready." -ForegroundColor Green
    exit 0
}
else {
    Write-Host ""
    Write-Host "💥 Stage-0 verification FAILED!" -ForegroundColor Red
    Write-Host "$($script:ChecksFailed) check(s) failed. Please address the issues above." -ForegroundColor Red
    exit 1
}
