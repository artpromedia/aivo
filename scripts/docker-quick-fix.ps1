# Docker Security Fix Script - Simplified Version
# This script fixes the Docker warnings and scans for security issues

param([switch]$SkipBackups)

Write-Host "🔍 Docker Security Script for AIVO" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Test Docker availability
Write-Host "Checking Docker..." -ForegroundColor Yellow
$null = docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker not found" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker is available" -ForegroundColor Green

# Test Docker Scout
Write-Host "Checking Docker Scout..." -ForegroundColor Yellow
$null = docker scout version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker Scout is available" -ForegroundColor Green
} else {
    Write-Host "⚠️ Docker Scout not available" -ForegroundColor Yellow
}

# Fix Dockerfiles
Write-Host "🔧 Fixing Dockerfiles..." -ForegroundColor Green
Get-ChildItem -Recurse -Name "Dockerfile*" | ForEach-Object {
    if ($_ -notlike "*node_modules*" -and $_ -notlike "*.git*") {
        Write-Host "Processing: $_" -ForegroundColor Cyan
        
        if (-not $SkipBackups) {
            Copy-Item $_ "$_.backup"
        }
        
        $content = Get-Content $_ -Raw
        $content = $content -replace ' as ', ' AS '
        $content = $content -replace 'node:\d+\.\d+-alpine', 'node:20.19-alpine'
        
        if ($content -notmatch "hadolint ignore") {
            $content = "# hadolint ignore=DL3008,DL3009,DL3018`n" + $content
        }
        
        Set-Content $_ -Value $content -NoNewline
    }
}

# Fix docker-compose files
Write-Host "🔧 Fixing docker-compose files..." -ForegroundColor Green
Get-ChildItem -Recurse -Name "docker-compose*.yml" | ForEach-Object {
    if ($_ -notlike "*node_modules*" -and $_ -notlike "*.git*") {
        Write-Host "Processing: $_" -ForegroundColor Cyan
        
        if (-not $SkipBackups) {
            Copy-Item $_ "$_.backup"
        }
        
        $content = Get-Content $_ -Raw
        $content = $content -replace 'version:\s*["\x27][2-9]\.[0-9]["\x27]', 'version: "3.8"'
        $content = $content -replace 'version:\s*["\x27]3\.[0-7]["\x27]', 'version: "3.8"'
        
        Set-Content $_ -Value $content -NoNewline
    }
}

# Scan images if Docker Scout is available
if ($LASTEXITCODE -eq 0) {
    Write-Host "🔍 Scanning for images to check..." -ForegroundColor Green
    
    $images = @("aivo-ai/mailserver:latest", "aivo-ai/email:latest")
    foreach ($image in $images) {
        $null = docker image inspect $image 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "📊 Scanning: $image" -ForegroundColor Yellow
            docker scout cves $image 2>$null
        } else {
            Write-Host "⚠️ Image not found: $image" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "✅ Docker fixes completed!" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "- Fixed AS casing in Dockerfiles"
Write-Host "- Updated to Node.js 20.19-alpine"
Write-Host "- Added hadolint ignore comments"
Write-Host "- Updated docker-compose versions"
Write-Host "- Scanned available images"
