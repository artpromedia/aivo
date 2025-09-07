#!/usr/bin/env powershell

# Script to test the Kong API Gateway Docker Compose setup

Write-Host "Testing Kong API Gateway Docker Compose Setup..." -ForegroundColor Blue

# Check if docker compose is available (Docker Desktop 4.45.0+)
if (!(Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Test if docker compose command works
try {
    docker compose version | Out-Null
    $composeCmd = "docker compose"
} catch {
    # Fallback to docker-compose for older versions
    if (!(Get-Command "docker-compose" -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Neither 'docker compose' nor 'docker-compose' found." -ForegroundColor Red
        exit 1
    }
    $composeCmd = "docker-compose"
}

Write-Host "Using: $composeCmd" -ForegroundColor Gray

# Change to gateway directory
Set-Location "apps\gateway"

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
    Set-Location "..\.."
    exit 0
}

Write-Host ""
Write-Host "1. Validating Docker Compose configuration..." -ForegroundColor Cyan
& $composeCmd config --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Compose configuration is invalid" -ForegroundColor Red
    Set-Location "..\.."
    exit 1
}
Write-Host "✓ Docker Compose configuration is valid" -ForegroundColor Green

Write-Host ""
Write-Host "2. Starting services..." -ForegroundColor Cyan
& $composeCmd up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    Set-Location "..\.."
    exit 1
}
Write-Host "✓ Services started successfully" -ForegroundColor Green

Write-Host ""
Write-Host "3. Waiting for Kong to be ready..." -ForegroundColor Cyan
Write-Host "   Initializing Kong database..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Initialize Kong database
& $composeCmd run --rm kong kong migrations bootstrap
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Database migration may have already been completed" -ForegroundColor Yellow
}

Write-Host "   Waiting for Kong to start..." -ForegroundColor Gray
Start-Sleep -Seconds 20

Write-Host ""
Write-Host "4. Testing Kong health..." -ForegroundColor Cyan

# Test Kong Admin API
try {
    $kongResponse = Invoke-WebRequest -Uri "http://localhost:8001" -UseBasicParsing -TimeoutSec 10
    Write-Host "✓ Kong Admin API is responding" -ForegroundColor Green
} catch {
    Write-Host "❌ Kong Admin API is not responding: $_" -ForegroundColor Red
}

# Test Kong Proxy
try {
    $proxyResponse = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing -TimeoutSec 10
    Write-Host "⚠️  Kong Proxy returned: $($proxyResponse.StatusCode) (expected without routes)" -ForegroundColor Yellow
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "✓ Kong Proxy is responding (404 expected without routes)" -ForegroundColor Green
    } else {
        Write-Host "❌ Kong Proxy error: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "5. Service Status:" -ForegroundColor Cyan
& $composeCmd ps

Write-Host ""
Write-Host "===========================================" -ForegroundColor Blue
Write-Host "Kong API Gateway Test Complete!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Blue

Write-Host ""
Write-Host "Available endpoints:" -ForegroundColor Yellow
Write-Host "  Kong Admin API: http://localhost:8001" -ForegroundColor White
Write-Host "  Kong Proxy: http://localhost:8000" -ForegroundColor White

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  - Configure Kong routes and services via Admin API" -ForegroundColor White
Write-Host "  - Add your microservices as upstream targets" -ForegroundColor White
Write-Host "  - Test API routing through Kong proxy" -ForegroundColor White

Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  Stop services: $composeCmd down" -ForegroundColor White
Write-Host "  View logs: $composeCmd logs -f" -ForegroundColor White
Write-Host "  Restart Kong: $composeCmd restart kong" -ForegroundColor White

# Return to original directory
Set-Location "..\.."
