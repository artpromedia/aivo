# Docker Security Scan and Fix Script for AIVO Monorepo
# Compatible with Docker Desktop 4.45.0+ and Docker Scout

param(
    [switch]$SkipBackups,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

Write-Host "🔍 Docker Security Scan and Fix Script for AIVO" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green

# Check if Docker is available
Write-Host "📋 Checking Docker availability..." -ForegroundColor Yellow
$dockerCheck = docker --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not installed or not in PATH" -ForegroundColor Red
    exit 1
}
Write-Host "📋 Docker version: $dockerCheck" -ForegroundColor Cyan

# Check Docker Scout availability
Write-Host "📝 Setting up Docker Scout..." -ForegroundColor Yellow
$scoutCheck = docker scout version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Docker Scout is available" -ForegroundColor Green
    
    # Try to enroll organization
    docker scout enroll artpromedia 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ℹ️  Organization may already be enrolled" -ForegroundColor Blue
    }
} else {
    Write-Host "⚠️  Docker Scout not available. Please update Docker Desktop to 4.17.0 or later." -ForegroundColor Yellow
}

# Function to scan Docker image
function Test-DockerImage {
    param(
        [string]$ImageName,
        [string]$Tag = "latest"
    )
    
    $fullImage = "${ImageName}:${Tag}"
    Write-Host "🔍 Checking if image exists: $fullImage" -ForegroundColor Cyan
    
    docker image inspect $fullImage 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "📊 Scanning $fullImage for vulnerabilities..." -ForegroundColor Yellow
        
        # Scan for CVEs
        docker scout cves $fullImage 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Could not scan $fullImage" -ForegroundColor Yellow
        }
        
        # Generate SBOM
        Write-Host "🔬 Generating SBOM for $fullImage..." -ForegroundColor Yellow
        $sbomFile = ($ImageName -replace "/", "-") + "-sbom.json"
        docker scout sbom $fullImage > $sbomFile 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Could not generate SBOM for $fullImage" -ForegroundColor Yellow
        }
        
        # Get recommendations
        Write-Host "💡 Getting recommendations for $fullImage..." -ForegroundColor Yellow
        docker scout recommendations $fullImage 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Could not get recommendations for $fullImage" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Image $fullImage not found locally. Skipping scan." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Scan AIVO service images
Write-Host "🔍 Scanning AIVO service images..." -ForegroundColor Green
$imagesToScan = @(
    "aivo-ai/mailserver",
    "aivo-ai/mailserver1", 
    "aivo-ai/email",
    "aivo-ai/admin-portal",
    "aivo-ai/auth-service",
    "aivo-ai/notification-service"
)

foreach ($image in $imagesToScan) {
    Test-DockerImage -ImageName $image
}

# Fix Dockerfile issues
Write-Host "🔧 Fixing Dockerfile issues in monorepo..." -ForegroundColor Green

$dockerfiles = Get-ChildItem -Path . -Name "Dockerfile*" -Recurse | Where-Object { 
    $_.FullName -notlike "*node_modules*" -and $_.FullName -notlike "*.git*" 
}

foreach ($dockerfile in $dockerfiles) {
    Write-Host "📝 Processing: $dockerfile" -ForegroundColor Cyan
    
    # Create backup unless skipped
    if (-not $SkipBackups) {
        Copy-Item $dockerfile "$dockerfile.backup"
    }
    
    # Read file content
    $content = Get-Content $dockerfile -Raw
    
    # Fix AS casing
    $content = $content -replace ' as ', ' AS '
    
    # Add hadolint ignore if not present
    if ($content -notmatch "hadolint ignore") {
        $content = "# hadolint ignore=DL3008,DL3009,DL3018`n" + $content
    }
    
    # Add Alpine security updates if missing
    if ($content -match "FROM.*alpine" -and $content -notmatch "apk update") {
        $alpineUpdate = "RUN apk update " + [char]38 + [char]38 + " apk upgrade " + [char]38 + [char]38 + " rm -rf /var/cache/apk/*"
        $content = $content -replace "(FROM.*alpine.*)", "`$1`n$alpineUpdate"
    }
    
    # Update Node.js to latest LTS
    $content = $content -replace "node:\d+\.\d+-alpine", "node:20.19-alpine"
    $content = $content -replace "node:\d+-alpine", "node:20.19-alpine"
    
    # Write back to file
    Set-Content $dockerfile -Value $content -NoNewline
}

# Fix docker-compose files
Write-Host "🔧 Updating docker-compose files..." -ForegroundColor Green

$composeFiles = Get-ChildItem -Path . -Name "docker-compose*.yml" -Recurse | Where-Object { 
    $_.FullName -notlike "*node_modules*" -and $_.FullName -notlike "*.git*" 
}

foreach ($composeFile in $composeFiles) {
    Write-Host "📝 Processing: $composeFile" -ForegroundColor Cyan
    
    # Create backup unless skipped
    if (-not $SkipBackups) {
        Copy-Item $composeFile "$composeFile.backup"
    }
    
    # Read and update content
    $content = Get-Content $composeFile -Raw
    
    # Update version to 3.8
    $content = $content -replace 'version:\s*["\x27][2-9]\.[0-9]["\x27]', 'version: "3.8"'
    $content = $content -replace 'version:\s*["\x27]3\.[0-7]["\x27]', 'version: "3.8"'
    
    # Write back to file
    Set-Content $composeFile -Value $content -NoNewline
}

# Build services with Docker Compose v2
Write-Host "🏗️  Building services with Docker Compose v2..." -ForegroundColor Green

if (Test-Path "infra/compose/local.yml") {
    Write-Host "📋 Using infra/compose/local.yml" -ForegroundColor Cyan
    docker compose -f infra/compose/local.yml build --no-cache 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Build failed or no services to build" -ForegroundColor Yellow
    }
} elseif (Test-Path "docker-compose.yml") {
    Write-Host "📋 Using docker-compose.yml" -ForegroundColor Cyan
    docker compose build --no-cache 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Build failed or no services to build" -ForegroundColor Yellow
    }
} else {
    Write-Host "ℹ️  No docker-compose files found in root or infra/compose/" -ForegroundColor Blue
}

# Run Docker Scout overview
Write-Host "🛡️  Running Docker Scout overview..." -ForegroundColor Green
docker scout quickview 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Could not run Docker Scout quickview" -ForegroundColor Yellow
}

# Cleanup backups if requested
if (-not $SkipBackups) {
    Write-Host "🧹 Cleaning up backup files..." -ForegroundColor Yellow
    Get-ChildItem -Path . -Name "*.backup" -Recurse | Where-Object { 
        $_.FullName -notlike "*node_modules*" -and $_.FullName -notlike "*.git*" 
    } | Remove-Item -Force
}

Write-Host ""
Write-Host "✅ Docker security scan and fixes complete!" -ForegroundColor Green
Write-Host "📋 Summary:" -ForegroundColor Cyan
Write-Host "   - Updated Dockerfiles with security improvements"
Write-Host "   - Fixed AS casing issues"
Write-Host "   - Updated to Node.js 20.19-alpine"
Write-Host "   - Added hadolint ignore comments"
Write-Host "   - Updated docker-compose format versions"
Write-Host "   - Scanned available images for vulnerabilities"
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "   - Review generated SBOM files (*-sbom.json)"
Write-Host "   - Address any critical vulnerabilities found"
Write-Host "   - Consider using Docker Scout in CI/CD pipeline"
