#!/usr/bin/env powershell

# Script to test the Docker Compose setup for Gateway Services

Write-Host "Testing Gateway Services Docker Compose Setup..." -ForegroundColor Blue

# Check if docker-compose is available
if (!(Get-Command "docker-compose" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ docker-compose not found. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file. Please edit it with your values." -ForegroundColor Green
    Write-Host ""
    Write-Host "Edit the .env file and set:" -ForegroundColor Cyan
    Write-Host "  KONG_PG_PASSWORD=your_secure_password" -ForegroundColor White
    Write-Host ""
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "1. Validating Docker Compose configuration..." -ForegroundColor Cyan
docker-compose config --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Compose configuration is invalid" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker Compose configuration is valid" -ForegroundColor Green

Write-Host ""
Write-Host "2. Building custom images..." -ForegroundColor Cyan
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build images" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Images built successfully" -ForegroundColor Green

Write-Host ""
Write-Host "3. Starting services..." -ForegroundColor Cyan
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Services started successfully" -ForegroundColor Green

Write-Host ""
Write-Host "4. Waiting for services to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "5. Testing service health..." -ForegroundColor Cyan

# Test Kong Admin API
try {
    $kongResponse = Invoke-WebRequest -Uri "http://localhost:8001" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Kong Admin API is responding" -ForegroundColor Green
} catch {
    Write-Host "❌ Kong Admin API is not responding: $_" -ForegroundColor Red
}

# Test Kong Proxy
try {
    $proxyResponse = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Kong Proxy is responding" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Kong Proxy returned error (expected without routes): $_" -ForegroundColor Yellow
}

# Test Mailserver Health
try {
    $mailResponse = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Mailserver health endpoint is responding" -ForegroundColor Green
} catch {
    Write-Host "❌ Mailserver health endpoint is not responding: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "6. Service Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "===========================================" -ForegroundColor Blue
Write-Host "Gateway Services Test Complete!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Blue

Write-Host ""
Write-Host "Available endpoints:" -ForegroundColor Yellow
Write-Host "  Kong Admin API: http://localhost:8001" -ForegroundColor White
Write-Host "  Kong Proxy: http://localhost:8000" -ForegroundColor White
Write-Host "  Mailserver Health: http://localhost:8080/health" -ForegroundColor White
Write-Host "  SMTP Port: localhost:25" -ForegroundColor White
Write-Host "  SMTP Submission: localhost:587" -ForegroundColor White

Write-Host ""
Write-Host "To stop services: docker-compose down" -ForegroundColor Cyan
Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Cyan
