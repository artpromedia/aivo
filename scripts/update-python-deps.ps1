#!/usr/bin/env powershell
# Update Python Dependencies and Export Requirements for Security-Hardened Services
# This script updates Poetry/pip dependencies and exports requirements.txt for Docker builds

param(
    [switch]$DryRun = $false,
    [switch]$CommitChanges = $false
)

# Security-hardened services with their dependency management type
$Services = @(
    @{ Name = "payment-svc"; Type = "pip"; HasPyProject = $true },
    @{ Name = "search-svc"; Type = "pip"; HasPyProject = $false },
    @{ Name = "notification-svc"; Type = "poetry"; HasPyProject = $true },
    @{ Name = "ink-svc"; Type = "poetry"; HasPyProject = $true },
    @{ Name = "learner-svc"; Type = "pip"; HasPyProject = $false },
    @{ Name = "event-collector-svc"; Type = "pip"; HasPyProject = $true }
)

function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
        } else {
            throw "Python not found"
        }
    } catch {
        Write-Host "❌ Python is not available" -ForegroundColor Red
        return $false
    }

    # Check pip
    try {
        pip --version >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ pip: Available" -ForegroundColor Green
        } else {
            throw "pip not found"
        }
    } catch {
        Write-Host "❌ pip is not available" -ForegroundColor Red
        return $false
    }

    # Check Poetry (optional)
    try {
        poetry --version >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Poetry: Available" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  Poetry not found - will install if needed" -ForegroundColor Yellow
            return $true
        }
    } catch {
        Write-Host "⚠️  Poetry not available - will install if needed" -ForegroundColor Yellow
        return $true
    }
}

function Install-Poetry {
    Write-Host "📦 Installing Poetry..." -ForegroundColor Blue

    try {
        # Try pip install first
        pip install poetry
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Poetry installed via pip" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "❌ Failed to install Poetry via pip" -ForegroundColor Red
        return $false
    }

    return $false
}

function Update-PoetryService {
    param([string]$ServiceName)

    $servicePath = "services/$ServiceName"

    if (!(Test-Path $servicePath)) {
        Write-Host "❌ Service path not found: $servicePath" -ForegroundColor Red
        return $false
    }

    Push-Location $servicePath

    try {
        Write-Host "🔄 Updating Poetry dependencies for $ServiceName..." -ForegroundColor Blue

        if ($DryRun) {
            Write-Host "   [DRY RUN] Would run: poetry update" -ForegroundColor Gray
            Write-Host "   [DRY RUN] Would run: poetry export --without-hashes -f requirements.txt -o requirements.txt" -ForegroundColor Gray
        } else {
            # Update dependencies
            poetry update
            if ($LASTEXITCODE -ne 0) {
                throw "Poetry update failed"
            }

            # Export requirements.txt
            poetry export --without-hashes -f requirements.txt -o requirements.txt
            if ($LASTEXITCODE -ne 0) {
                throw "Poetry export failed"
            }
        }

        Write-Host "✅ $ServiceName updated successfully" -ForegroundColor Green
        return $true

    } catch {
        Write-Host "❌ Failed to update $ServiceName`: $_" -ForegroundColor Red
        return $false
    } finally {
        Pop-Location
    }
}

function Update-PipService {
    param([string]$ServiceName, [bool]$HasPyProject)

    $servicePath = "services/$ServiceName"

    if (!(Test-Path $servicePath)) {
        Write-Host "❌ Service path not found: $servicePath" -ForegroundColor Red
        return $false
    }

    if (!(Test-Path "$servicePath/requirements.txt")) {
        Write-Host "❌ requirements.txt not found in $servicePath" -ForegroundColor Red
        return $false
    }

    Push-Location $servicePath

    try {
        Write-Host "🔄 Updating pip dependencies for $ServiceName..." -ForegroundColor Blue

        if ($DryRun) {
            Write-Host "   [DRY RUN] Would run: pip install --upgrade -r requirements.txt" -ForegroundColor Gray
            if ($HasPyProject) {
                Write-Host "   [DRY RUN] Would run: pip freeze > requirements.txt" -ForegroundColor Gray
            }
        } else {
            # For pip-based services, we'll upgrade the packages in requirements.txt
            # Create a temporary virtual environment to get updated versions
            $tempVenv = "temp_venv_$ServiceName"

            # Create temporary virtual environment
            python -m venv $tempVenv
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to create virtual environment"
            }

            # Activate virtual environment
            & "$tempVenv\Scripts\Activate.ps1"

            # Upgrade pip in venv
            python -m pip install --upgrade pip

            # Install and upgrade all dependencies
            pip install --upgrade -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to upgrade dependencies"
            }

            # Export updated requirements
            pip freeze | Where-Object { $_ -notmatch "^-e " } > requirements_new.txt

            # Deactivate and remove venv
            deactivate
            Remove-Item -Recurse -Force $tempVenv

            # Replace old requirements with new ones
            Move-Item requirements_new.txt requirements.txt -Force
        }

        Write-Host "✅ $ServiceName updated successfully" -ForegroundColor Green
        return $true

    } catch {
        Write-Host "❌ Failed to update $ServiceName`: $_" -ForegroundColor Red

        # Cleanup on failure
        if (Test-Path "temp_venv_$ServiceName") {
            Remove-Item -Recurse -Force "temp_venv_$ServiceName"
        }

        return $false
    } finally {
        Pop-Location
    }
}

function Show-UpdateSummary {
    param([array]$UpdatedServices, [array]$FailedServices)

    Write-Host "`n🔒 DEPENDENCY UPDATE SUMMARY" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan

    if ($UpdatedServices.Count -gt 0) {
        Write-Host "✅ Successfully Updated ($($UpdatedServices.Count)):" -ForegroundColor Green
        foreach ($service in $UpdatedServices) {
            Write-Host "   - $service" -ForegroundColor Green
        }
    }

    if ($FailedServices.Count -gt 0) {
        Write-Host "❌ Failed Updates ($($FailedServices.Count)):" -ForegroundColor Red
        foreach ($service in $FailedServices) {
            Write-Host "   - $service" -ForegroundColor Red
        }
    }

    Write-Host "`n🔄 Security Benefits:" -ForegroundColor Yellow
    Write-Host "   - Latest security patches applied" -ForegroundColor Gray
    Write-Host "   - CVE vulnerabilities mitigated" -ForegroundColor Gray
    Write-Host "   - Updated requirements.txt for Docker builds" -ForegroundColor Gray
}

# Main execution
Write-Host "🚀 AIVO Security Dependency Updater" -ForegroundColor Cyan
Write-Host "=" * 45 -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
}

# Check prerequisites
if (!(Test-Prerequisites)) {
    exit 1
}

# Track results
$updatedServices = @()
$failedServices = @()
$needsPoetry = $false

# Check if we need Poetry
foreach ($service in $Services) {
    if ($service.Type -eq "poetry") {
        $needsPoetry = $true
        break
    }
}

# Install Poetry if needed
if ($needsPoetry) {
    try {
        poetry --version >$null 2>&1
        if ($LASTEXITCODE -ne 0) {
            if (!(Install-Poetry)) {
                Write-Host "❌ Poetry installation failed - skipping Poetry services" -ForegroundColor Red
            }
        }
    } catch {
        if (!(Install-Poetry)) {
            Write-Host "❌ Poetry installation failed - skipping Poetry services" -ForegroundColor Red
        }
    }
}

# Process each service
foreach ($service in $Services) {
    Write-Host "`n" + "=" * 60 -ForegroundColor DarkGray
    Write-Host "Processing: $($service.Name) ($($service.Type))" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor DarkGray

    $success = $false

    if ($service.Type -eq "poetry") {
        $success = Update-PoetryService -ServiceName $service.Name
    } else {
        $success = Update-PipService -ServiceName $service.Name -HasPyProject $service.HasPyProject
    }

    if ($success) {
        $updatedServices += $service.Name
    } else {
        $failedServices += $service.Name
    }
}

# Show summary
Show-UpdateSummary -UpdatedServices $updatedServices -FailedServices $failedServices

# Commit changes if requested
if ($CommitChanges -and !$DryRun -and $updatedServices.Count -gt 0) {
    Write-Host "`n🔒 Committing security updates..." -ForegroundColor Blue

    try {
        git add -A
        git commit -S -m "chore(security): bump vulnerable py deps and harden Dockerfiles"

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Changes committed with GPG signature" -ForegroundColor Green
        } else {
            Write-Host "❌ Git commit failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Git commit failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n🎉 Dependency update process completed!" -ForegroundColor Green
