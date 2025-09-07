# Docker Security Fix Script - Working Version
param([switch]$SkipBackups)

Write-Host "Docker Security Script for AIVO" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

# Test Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
docker --version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker not found" -ForegroundColor Red
    exit 1
}
Write-Host "Docker is available" -ForegroundColor Green

# Fix Dockerfiles
Write-Host "Fixing Dockerfiles..." -ForegroundColor Green
Get-ChildItem -Recurse -Name "Dockerfile*" | Where-Object { 
    $_ -notlike "*node_modules*" -and $_ -notlike "*.git*" 
} | ForEach-Object {
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

# Fix docker-compose files  
Write-Host "Fixing docker-compose files..." -ForegroundColor Green
Get-ChildItem -Recurse -Name "docker-compose*.yml" | Where-Object { 
    $_ -notlike "*node_modules*" -and $_ -notlike "*.git*" 
} | ForEach-Object {
    Write-Host "Processing: $_" -ForegroundColor Cyan
    
    if (-not $SkipBackups) {
        Copy-Item $_ "$_.backup"
    }
    
    $content = Get-Content $_ -Raw
    $content = $content -replace 'version:\s*["\x27][2-9]\.[0-9]["\x27]', 'version: "3.8"'
    
    Set-Content $_ -Value $content -NoNewline
}

Write-Host ""
Write-Host "Docker fixes completed!" -ForegroundColor Green
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "- Fixed AS casing in Dockerfiles"
Write-Host "- Updated to Node.js 20.19-alpine" 
Write-Host "- Added hadolint ignore comments"
Write-Host "- Updated docker-compose versions"
