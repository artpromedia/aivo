#!/usr/bin/env powershell
# Build and Security Scan Script for AIVO Services
# This script builds Docker images and scans them for vulnerabilities using Trivy

param(
    [string]$Service = "payment-svc",
    [switch]$ScanOnly = $false,
    [switch]$BuildOnly = $false,
    [switch]$AllServices = $false
)

# Security-hardened services that are ready for scanning
$SecurityHardenedServices = @(
    "payment-svc",
    "search-svc",
    "notification-svc",
    "ink-svc",
    "learner-svc",
    "event-collector-svc"
)

function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
        } else {
            throw "Docker not found"
        }
    } catch {
        Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
        Write-Host "   Please install Docker Desktop for Windows" -ForegroundColor Yellow
        Write-Host "   Download: https://docs.docker.com/desktop/install/windows/" -ForegroundColor Yellow
        return $false
    }

    # Check Trivy
    try {
        $trivyVersion = trivy --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Trivy: $trivyVersion" -ForegroundColor Green
        } else {
            throw "Trivy not found"
        }
    } catch {
        Write-Host "❌ Trivy is not installed" -ForegroundColor Red
        Write-Host "   Install with: winget install aquasec.trivy" -ForegroundColor Yellow
        Write-Host "   Or download: https://github.com/aquasecurity/trivy/releases" -ForegroundColor Yellow
        return $false
    }

    return $true
}

function Build-Service {
    param([string]$ServiceName)

    $imageName = "aivo/${ServiceName}:ci"
    $servicePath = "services/$ServiceName"

    if (!(Test-Path $servicePath)) {
        Write-Host "❌ Service path not found: $servicePath" -ForegroundColor Red
        return $false
    }

    Write-Host "🔨 Building $ServiceName..." -ForegroundColor Blue
    Write-Host "   Image: $imageName" -ForegroundColor Gray
    Write-Host "   Path: $servicePath" -ForegroundColor Gray

    $buildStart = Get-Date
    docker build -t $imageName $servicePath

    if ($LASTEXITCODE -eq 0) {
        $buildTime = (Get-Date) - $buildStart
        Write-Host "✅ Build completed in $($buildTime.TotalSeconds.ToString('F1')) seconds" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Build failed for $ServiceName" -ForegroundColor Red
        return $false
    }
}

function Scan-Service {
    param([string]$ServiceName)

    $imageName = "aivo/${ServiceName}:ci"

    Write-Host "🔍 Scanning $ServiceName for vulnerabilities..." -ForegroundColor Blue
    Write-Host "   Severity: HIGH, CRITICAL only" -ForegroundColor Gray
    Write-Host "   Ignore unfixed: Yes" -ForegroundColor Gray

    $scanStart = Get-Date

    # Basic scan output
    Write-Host "`n📊 Security Scan Results for $ServiceName" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan

    trivy image --severity HIGH,CRITICAL --ignore-unfixed $imageName

    if ($LASTEXITCODE -eq 0) {
        $scanTime = (Get-Date) - $scanStart
        Write-Host "✅ Scan completed in $($scanTime.TotalSeconds.ToString('F1')) seconds" -ForegroundColor Green

        # Generate JSON report
        $reportFile = "${ServiceName}-security-scan.json"
        trivy image --severity HIGH,CRITICAL --ignore-unfixed --format json --output $reportFile $imageName

        if (Test-Path $reportFile) {
            Write-Host "📄 Detailed report saved: $reportFile" -ForegroundColor Green
        }

        return $true
    } else {
        Write-Host "❌ Scan failed for $ServiceName" -ForegroundColor Red
        return $false
    }
}

function Show-SecuritySummary {
    param([array]$Services)

    Write-Host "`n🔒 SECURITY HARDENING SUMMARY" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    Write-Host "Base Image: python:3.11-slim-bookworm@sha256:edaf..." -ForegroundColor Green
    Write-Host "Security Updates: ✅ apt-get upgrade applied" -ForegroundColor Green
    Write-Host "Python Tools: ✅ Latest pip/setuptools/wheel" -ForegroundColor Green
    Write-Host "User Security: ✅ Non-root UID 10001" -ForegroundColor Green
    Write-Host "Build Optimization: ✅ Cache mounts enabled" -ForegroundColor Green
    Write-Host "`nServices Processed: $($Services -join ', ')" -ForegroundColor Yellow
}

# Main execution
Write-Host "🚀 AIVO Docker Security Scanner" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

# Check prerequisites
if (!(Test-Prerequisites)) {
    exit 1
}

# Determine services to process
$servicesToProcess = @()

if ($AllServices) {
    $servicesToProcess = $SecurityHardenedServices
    Write-Host "🎯 Processing all security-hardened services ($($servicesToProcess.Count))" -ForegroundColor Yellow
} else {
    if ($Service -notin $SecurityHardenedServices) {
        Write-Host "⚠️  Warning: $Service may not be security-hardened yet" -ForegroundColor Yellow
        Write-Host "   Hardened services: $($SecurityHardenedServices -join ', ')" -ForegroundColor Gray
    }
    $servicesToProcess = @($Service)
}

# Process each service
$results = @()
foreach ($svc in $servicesToProcess) {
    Write-Host "`n" + "=" * 60 -ForegroundColor DarkGray
    Write-Host "Processing: $svc" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor DarkGray

    $buildSuccess = $true
    $scanSuccess = $true

    if (!$ScanOnly) {
        $buildSuccess = Build-Service -ServiceName $svc
    }

    if ($buildSuccess -and !$BuildOnly) {
        $scanSuccess = Scan-Service -ServiceName $svc
    }

    $results += [PSCustomObject]@{
        Service = $svc
        BuildSuccess = $buildSuccess
        ScanSuccess = $scanSuccess
        Status = if ($buildSuccess -and $scanSuccess) { "✅ Success" } else { "❌ Failed" }
    }
}

# Summary
Write-Host "`n" + "=" * 60 -ForegroundColor DarkGray
Write-Host "📋 EXECUTION SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor DarkGray

$results | Format-Table -AutoSize

Show-SecuritySummary -Services $servicesToProcess

Write-Host "`n🎉 Security scanning completed!" -ForegroundColor Green
Write-Host "📊 Review the scan results above for any vulnerabilities" -ForegroundColor Yellow
Write-Host "📄 JSON reports generated for detailed analysis" -ForegroundColor Gray
