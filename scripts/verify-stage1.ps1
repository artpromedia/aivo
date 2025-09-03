# Stage-1 Compose Setup and Verification Script (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Stage-1 Docker Compose Setup and Verification" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Change to the repository root
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "📦 Starting all S1 services with Docker Compose..." -ForegroundColor Cyan
docker compose -f infra/compose/local.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start Docker Compose services" -ForegroundColor Red
    exit 1
}

Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "🔍 Running golden path verification..." -ForegroundColor Cyan

# Try to run verification script
$nodeAvailable = Get-Command node -ErrorAction SilentlyContinue
$tsNodeAvailable = Get-Command ts-node -ErrorAction SilentlyContinue

if ($nodeAvailable) {
    node scripts/verify-stage1.js
} elseif ($tsNodeAvailable) {
    ts-node scripts/verify-stage1.ts
} else {
    Write-Host "❌ Neither node nor ts-node found. Please install Node.js or ts-node." -ForegroundColor Red
    exit 1
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Stage-1 setup and verification complete!" -ForegroundColor Green
    Write-Host "🌐 Services are running on:" -ForegroundColor Cyan
    Write-Host "  - Kong Gateway: http://localhost:8000" -ForegroundColor White
    Write-Host "  - Admin Portal API: http://localhost:8091" -ForegroundColor White
    Write-Host "  - MailHog (Email UI): http://localhost:8025" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 To view logs: docker compose -f infra/compose/local.yml logs -f [service]" -ForegroundColor Yellow
    Write-Host "🛑 To stop: docker compose -f infra/compose/local.yml down" -ForegroundColor Yellow
} else {
    Write-Host "❌ Verification failed!" -ForegroundColor Red
    exit 1
}
