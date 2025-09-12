#!/usr/bin/env powershell
# Security Audit Script for AIVO Python Services
# This script performs comprehensive security audits using pip-audit and safety

param(
    [string]$Service = "payment-svc",
    [switch]$AllServices = $false,
    [switch]$InstallTools = $false,
    [switch]$UsePoetry = $false
)

# Security-hardened services that are ready for auditing
$SecurityHardenedServices = @(
    @{ Name = "payment-svc"; Type = "pip"; Path = "services/payment-svc" },
    @{ Name = "search-svc"; Type = "pip"; Path = "services/search-svc" },
    @{ Name = "notification-svc"; Type = "poetry"; Path = "services/notification-svc" },
    @{ Name = "ink-svc"; Type = "poetry"; Path = "services/ink-svc" },
    @{ Name = "learner-svc"; Type = "pip"; Path = "services/learner-svc" },
    @{ Name = "event-collector-svc"; Type = "pip"; Path = "services/event-collector-svc" }
)

function Test-SecurityTools {
    Write-Host "🔍 Checking security audit tools..." -ForegroundColor Yellow

    $toolsAvailable = @()
    $toolsMissing = @()

    # Check pip-audit
    try {
        $pipAuditVersion = pip-audit --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ pip-audit: $pipAuditVersion" -ForegroundColor Green
            $toolsAvailable += "pip-audit"
        } else {
            throw "pip-audit not found"
        }
    } catch {
        Write-Host "❌ pip-audit not available" -ForegroundColor Red
        $toolsMissing += "pip-audit"
    }

    # Check safety
    try {
        $safetyVersion = safety --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ safety: $safetyVersion" -ForegroundColor Green
            $toolsAvailable += "safety"
        } else {
            throw "safety not found"
        }
    } catch {
        Write-Host "❌ safety not available" -ForegroundColor Red
        $toolsMissing += "safety"
    }

    # Check Poetry if needed
    if ($UsePoetry) {
        try {
            $poetryVersion = poetry --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ poetry: $poetryVersion" -ForegroundColor Green
                $toolsAvailable += "poetry"
            } else {
                throw "poetry not found"
            }
        } catch {
            Write-Host "❌ poetry not available" -ForegroundColor Red
            $toolsMissing += "poetry"
        }
    }

    return @{
        Available = $toolsAvailable
        Missing = $toolsMissing
        AllAvailable = ($toolsMissing.Count -eq 0)
    }
}

function Install-SecurityTools {
    Write-Host "📦 Installing security audit tools..." -ForegroundColor Blue

    $success = $true

    # Install pip-audit
    try {
        Write-Host "Installing pip-audit..." -ForegroundColor Gray
        pip install pip-audit
        if ($LASTEXITCODE -ne 0) {
            throw "pip-audit installation failed"
        }
    } catch {
        Write-Host "❌ Failed to install pip-audit: $_" -ForegroundColor Red
        $success = $false
    }

    # Install safety
    try {
        Write-Host "Installing safety..." -ForegroundColor Gray
        pip install safety
        if ($LASTEXITCODE -ne 0) {
            throw "safety installation failed"
        }
    } catch {
        Write-Host "❌ Failed to install safety: $_" -ForegroundColor Red
        $success = $false
    }

    return $success
}

function Export-PoetryRequirements {
    param([string]$ServicePath)

    if (!(Test-Path "$ServicePath/pyproject.toml")) {
        Write-Host "❌ No pyproject.toml found in $ServicePath" -ForegroundColor Red
        return $false
    }

    Push-Location $ServicePath

    try {
        Write-Host "📦 Exporting Poetry requirements..." -ForegroundColor Blue
        poetry export -f requirements.txt -o requirements.txt --without-hashes

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Requirements exported successfully" -ForegroundColor Green
            return $true
        } else {
            throw "Poetry export failed"
        }
    } catch {
        Write-Host "❌ Failed to export Poetry requirements: $_" -ForegroundColor Red
        return $false
    } finally {
        Pop-Location
    }
}

function Invoke-PipAudit {
    param([string]$RequirementsPath, [string]$ServiceName)

    Write-Host "🔍 Running pip-audit on $ServiceName..." -ForegroundColor Blue
    Write-Host "   Requirements: $RequirementsPath" -ForegroundColor Gray

    try {
        # Run pip-audit with detailed output
        Write-Host "`n📊 pip-audit Security Scan Results:" -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Cyan

        pip-audit -r $RequirementsPath --format=columns --progress-spinner=off

        $auditExitCode = $LASTEXITCODE

        # Also generate JSON report
        $reportFile = "${ServiceName}-pip-audit.json"
        pip-audit -r $RequirementsPath --format=json --output=$reportFile

        if (Test-Path $reportFile) {
            Write-Host "📄 Detailed report saved: $reportFile" -ForegroundColor Green
        }

        if ($auditExitCode -eq 0) {
            Write-Host "✅ No known vulnerabilities found!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  Vulnerabilities detected - see report above" -ForegroundColor Yellow
            return $false
        }

    } catch {
        Write-Host "❌ pip-audit failed: $_" -ForegroundColor Red
        return $false
    }
}

function Invoke-SafetyCheck {
    param([string]$RequirementsPath, [string]$ServiceName)

    Write-Host "🔍 Running safety check on $ServiceName..." -ForegroundColor Blue

    try {
        Write-Host "`n📊 Safety Security Scan Results:" -ForegroundColor Cyan
        Write-Host "=" * 50 -ForegroundColor Cyan

        safety check -r $RequirementsPath --full-report

        $safetyExitCode = $LASTEXITCODE

        # Generate JSON report
        $reportFile = "${ServiceName}-safety.json"
        safety check -r $RequirementsPath --json --output=$reportFile

        if (Test-Path $reportFile) {
            Write-Host "📄 Safety report saved: $reportFile" -ForegroundColor Green
        }

        if ($safetyExitCode -eq 0) {
            Write-Host "✅ No known vulnerabilities found!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️  Vulnerabilities detected - see report above" -ForegroundColor Yellow
            return $false
        }

    } catch {
        Write-Host "❌ safety check failed: $_" -ForegroundColor Red
        return $false
    }
}

function Audit-Service {
    param([hashtable]$ServiceInfo)

    $serviceName = $ServiceInfo.Name
    $serviceType = $ServiceInfo.Type
    $servicePath = $ServiceInfo.Path

    Write-Host "`n" + "=" * 60 -ForegroundColor DarkGray
    Write-Host "Auditing: $serviceName ($serviceType)" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor DarkGray

    if (!(Test-Path $servicePath)) {
        Write-Host "❌ Service path not found: $servicePath" -ForegroundColor Red
        return @{ Service = $serviceName; Success = $false; Reason = "Path not found" }
    }

    $requirementsPath = "$servicePath/requirements.txt"

    # Handle Poetry services
    if ($serviceType -eq "poetry") {
        if (!(Export-PoetryRequirements -ServicePath $servicePath)) {
            return @{ Service = $serviceName; Success = $false; Reason = "Poetry export failed" }
        }
    }

    # Check if requirements.txt exists
    if (!(Test-Path $requirementsPath)) {
        Write-Host "❌ requirements.txt not found: $requirementsPath" -ForegroundColor Red
        return @{ Service = $serviceName; Success = $false; Reason = "requirements.txt not found" }
    }

    # Run security audits
    $pipAuditSuccess = $true
    $safetySuccess = $true

    # pip-audit scan
    if ("pip-audit" -in $toolStatus.Available) {
        $pipAuditSuccess = Invoke-PipAudit -RequirementsPath $requirementsPath -ServiceName $serviceName
    }

    # safety scan
    if ("safety" -in $toolStatus.Available) {
        $safetySuccess = Invoke-SafetyCheck -RequirementsPath $requirementsPath -ServiceName $serviceName
    }

    $overallSuccess = $pipAuditSuccess -and $safetySuccess

    return @{
        Service = $serviceName
        Success = $overallSuccess
        PipAudit = $pipAuditSuccess
        Safety = $safetySuccess
    }
}

function Show-AuditSummary {
    param([array]$Results)

    Write-Host "`n🔒 SECURITY AUDIT SUMMARY" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan

    $successful = $Results | Where-Object { $_.Success }
    $failed = $Results | Where-Object { -not $_.Success }

    if ($successful.Count -gt 0) {
        Write-Host "✅ Clean Services ($($successful.Count)):" -ForegroundColor Green
        foreach ($result in $successful) {
            Write-Host "   - $($result.Service)" -ForegroundColor Green
        }
    }

    if ($failed.Count -gt 0) {
        Write-Host "⚠️  Services with Issues ($($failed.Count)):" -ForegroundColor Yellow
        foreach ($result in $failed) {
            $status = ""
            if ($result.PipAudit -eq $false) { $status += "pip-audit " }
            if ($result.Safety -eq $false) { $status += "safety " }
            Write-Host "   - $($result.Service): $status" -ForegroundColor Yellow
        }
    }

    Write-Host "`n📊 Security Scanning Tools Used:" -ForegroundColor Gray
    if ("pip-audit" -in $toolStatus.Available) {
        Write-Host "   - pip-audit: OSV database scanning" -ForegroundColor Gray
    }
    if ("safety" -in $toolStatus.Available) {
        Write-Host "   - safety: PyUp.io vulnerability database" -ForegroundColor Gray
    }
}

# Main execution
Write-Host "🚀 AIVO Security Audit Scanner" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

# Check/install tools
$script:toolStatus = Test-SecurityTools

if (!$toolStatus.AllAvailable -and $InstallTools) {
    if (!(Install-SecurityTools)) {
        Write-Host "❌ Failed to install required tools" -ForegroundColor Red
        exit 1
    }
    $script:toolStatus = Test-SecurityTools
}

if (!$toolStatus.AllAvailable) {
    Write-Host "⚠️  Some security tools are missing:" -ForegroundColor Yellow
    foreach ($tool in $toolStatus.Missing) {
        Write-Host "   - $tool" -ForegroundColor Red
    }
    Write-Host "Run with -InstallTools to install missing tools" -ForegroundColor Yellow
}

# Determine services to audit
$servicesToAudit = @()

if ($AllServices) {
    $servicesToAudit = $SecurityHardenedServices
    Write-Host "🎯 Auditing all security-hardened services ($($servicesToAudit.Count))" -ForegroundColor Yellow
} else {
    $serviceInfo = $SecurityHardenedServices | Where-Object { $_.Name -eq $Service }
    if ($serviceInfo) {
        $servicesToAudit = @($serviceInfo)
    } else {
        Write-Host "❌ Service '$Service' not found or not security-hardened" -ForegroundColor Red
        Write-Host "Available services: $($SecurityHardenedServices.Name -join ', ')" -ForegroundColor Gray
        exit 1
    }
}

# Run audits
$results = @()
foreach ($serviceInfo in $servicesToAudit) {
    $results += Audit-Service -ServiceInfo $serviceInfo
}

# Show summary
Show-AuditSummary -Results $results

Write-Host "`n🎉 Security audit completed!" -ForegroundColor Green
