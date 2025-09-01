# Monorepo Build Script (PowerShell equivalent to Makefile)
# =========================================================

param(
    [Parameter(Position=0)]
    [string]$Target = "help"
)

function Write-Header($text) {
    Write-Host "========================================"
    Write-Host $text -ForegroundColor Cyan
    Write-Host "========================================"
}

function Write-Step($text) {
    Write-Host "🔧 $text" -ForegroundColor Blue
}

function Write-Success($text) {
    Write-Host "✅ $text" -ForegroundColor Green
}

switch ($Target.ToLower()) {
    "help" {
        Write-Header "Monorepo Stage-0 Build Commands"
        Write-Host "Usage: .\build.ps1 [target]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Available targets:" -ForegroundColor White
        Write-Host "  help           Show this help message"
        Write-Host "  install        Install all dependencies"
        Write-Host "  verify         Run basic verification"
        Write-Host "  verify-all     Run complete Stage-0 verification"
        Write-Host "  stage0-verify  Run Stage-0 verification script"
        Write-Host "  test           Run all tests"
        Write-Host "  clean          Clean build artifacts"
    }

    "install" {
        Write-Header "Installing all dependencies"
        Write-Step "Installing Node.js dependencies..."
        corepack enable
        pnpm install
        
        Write-Step "Setting up Python environment..."
        python -m venv .venv
        .\.venv\Scripts\pip install -r services\hello-svc\requirements.txt
        
        Write-Success "All dependencies installed"
    }

    "verify" {
        Write-Header "Running basic verification"
        pnpm run lint
        pnpm run format:check
        Write-Success "Basic verification completed"
    }

    "verify-all" {
        Write-Header "Running complete Stage-0 verification"
        pnpm run verify-all
        Write-Success "Complete verification finished"
    }

    "stage0-verify" {
        Write-Header "Running Stage-0 verification script"
        .\scripts\verify-stage0.ps1
    }

    "test" {
        Write-Header "Running all tests"
        Write-Step "Testing hello-svc..."
        Set-Location services\hello-svc
        ..\..\..venv\Scripts\python -m pytest tests\ -v
        Set-Location ..\..
        Write-Success "All tests completed"
    }

    "clean" {
        Write-Header "Cleaning build artifacts"
        if (Test-Path node_modules) { Remove-Item -Recurse -Force node_modules }
        if (Test-Path .venv) { Remove-Item -Recurse -Force .venv }
        Write-Success "Cleanup completed"
    }

    default {
        Write-Host "Unknown target: $Target" -ForegroundColor Red
        Write-Host "Run '.\build.ps1 help' to see available targets" -ForegroundColor Yellow
        exit 1
    }
}
