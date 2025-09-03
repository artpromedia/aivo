#!/usr/bin/env powershell
# Quick verification script for working services

Write-Host "=== S1 Services Status Check ===" -ForegroundColor Green

# Test MailHog
Write-Host "`n1. Testing MailHog (Email UI)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8091" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ MailHog is working: http://localhost:8091" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ MailHog is not responding on port 8091" -ForegroundColor Red
}

# Test Admin Portal API
Write-Host "`n2. Testing Admin Portal API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8092/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Admin Portal API is working: http://localhost:8092" -ForegroundColor Green
        Write-Host "   API Docs: http://localhost:8092/docs" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Admin Portal API is not responding on port 8092" -ForegroundColor Red
}

# Test Kong Gateway
Write-Host "`n3. Testing Kong Gateway..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Kong Gateway is working: http://localhost:8002" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Kong Gateway is not responding on port 8002" -ForegroundColor Red
    Write-Host "   Note: Kong configuration needs to be fixed" -ForegroundColor Yellow
}

Write-Host "`n=== Summary ===" -ForegroundColor Green
Write-Host "Working URLs:" -ForegroundColor Cyan
Write-Host "• MailHog UI: http://localhost:8091" -ForegroundColor White
Write-Host "• Admin Portal API: http://localhost:8092" -ForegroundColor White
Write-Host "• Admin Portal Docs: http://localhost:8092/docs" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "• Fix Kong Gateway configuration" -ForegroundColor White
Write-Host "• Start PostgreSQL and Redis services" -ForegroundColor White
Write-Host "• Start remaining microservices" -ForegroundColor White
