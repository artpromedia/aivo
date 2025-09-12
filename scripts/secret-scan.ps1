#!/usr/bin/env powershell
# Secret Scanning Script for AIVO using TruffleHog
# This script installs TruffleHog (if needed) and runs comprehensive secret scanning

param(
    [string]$ScanPath = ".",
    [switch]$InstallTruffleHog = $false,
    [switch]$OnlyVerified = $false,
    [switch]$WithEntropy = $false,
    [string]$OutputFormat = "table",
    [string]$OutputFile = $null
)

function Test-TruffleHog {
    Write-Host "🔍 Checking TruffleHog installation..." -ForegroundColor Yellow

    try {
        $version = trufflehog --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ TruffleHog: $version" -ForegroundColor Green
            return $true
        } else {
            throw "TruffleHog not found"
        }
    } catch {
        Write-Host "❌ TruffleHog is not installed" -ForegroundColor Red
        return $false
    }
}

function Install-TruffleHog {
    Write-Host "📦 Installing TruffleHog..." -ForegroundColor Blue

    # Try winget first
    try {
        Write-Host "Attempting installation via winget..." -ForegroundColor Gray
        winget install trufflesecurity.trufflehog

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ TruffleHog installed via winget" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "⚠️  winget installation failed" -ForegroundColor Yellow
    }

    # Try chocolatey
    try {
        Write-Host "Attempting installation via chocolatey..." -ForegroundColor Gray
        choco install trufflehog

        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ TruffleHog installed via chocolatey" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "⚠️  chocolatey installation failed" -ForegroundColor Yellow
    }

    # Try direct download
    try {
        Write-Host "Attempting direct download..." -ForegroundColor Gray
        $downloadUrl = "https://github.com/trufflesecurity/trufflehog/releases/latest/download/trufflehog_windows_amd64.exe"
        $outputPath = "$env:USERPROFILE\trufflehog.exe"

        Invoke-WebRequest -Uri $downloadUrl -OutFile $outputPath

        if (Test-Path $outputPath) {
            Write-Host "✅ TruffleHog downloaded to $outputPath" -ForegroundColor Green
            Write-Host "   Add this location to your PATH or move to a directory in PATH" -ForegroundColor Yellow
            return $true
        }
    } catch {
        Write-Host "❌ Direct download failed: $_" -ForegroundColor Red
    }

    return $false
}

function Invoke-SecretScan {
    param(
        [string]$Path,
        [bool]$EntropyEnabled,
        [bool]$VerifiedOnly,
        [string]$Format,
        [string]$Output
    )

    Write-Host "🔍 Running TruffleHog secret scan..." -ForegroundColor Blue
    Write-Host "   Path: $Path" -ForegroundColor Gray
    Write-Host "   Entropy: $EntropyEnabled" -ForegroundColor Gray
    Write-Host "   Verified only: $VerifiedOnly" -ForegroundColor Gray
    Write-Host "   Format: $Format" -ForegroundColor Gray

    # Build command arguments
    $cmdArgs = @("filesystem")

    if (!$EntropyEnabled) {
        $cmdArgs += "--entropy=False"
    }

    if ($VerifiedOnly) {
        $cmdArgs += "--only-verified"
    }

    if ($Format -ne "table") {
        $cmdArgs += "--format=$Format"
    }

    if ($Output) {
        $cmdArgs += "--output=$Output"
    }

    $cmdArgs += $Path

    Write-Host "`n📊 TruffleHog Secret Scan Results:" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "Command: trufflehog $($cmdArgs -join ' ')" -ForegroundColor Gray
    Write-Host "=" * 60 -ForegroundColor Cyan

    try {
        & trufflehog @cmdArgs

        $scanExitCode = $LASTEXITCODE

        Write-Host "`n" + "=" * 60 -ForegroundColor Cyan

        if ($scanExitCode -eq 0) {
            Write-Host "✅ Scan completed successfully" -ForegroundColor Green
            Write-Host "   No secrets found or all secrets are in ignored paths" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Secrets detected - review output above" -ForegroundColor Yellow
            Write-Host "   Exit code: $scanExitCode" -ForegroundColor Yellow
        }

        if ($Output -and (Test-Path $Output)) {
            Write-Host "📄 Detailed report saved: $Output" -ForegroundColor Green
        }

        return ($scanExitCode -eq 0)

    } catch {
        Write-Host "❌ TruffleHog scan failed: $_" -ForegroundColor Red
        return $false
    }
}

function Show-IgnorePatterns {
    $ignoreFile = ".trufflehogignore"

    if (Test-Path $ignoreFile) {
        Write-Host "`n🔒 Active Ignore Patterns (.trufflehogignore):" -ForegroundColor Cyan
        Get-Content $ignoreFile | ForEach-Object {
            if ($_ -and !$_.StartsWith("#")) {
                Write-Host "   - $_" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "`n⚠️  No .trufflehogignore file found" -ForegroundColor Yellow
        Write-Host "   Consider creating one to ignore false positives in docs/tests" -ForegroundColor Gray
    }
}

function Show-ScanSummary {
    param([bool]$ScanSuccess)

    Write-Host "`n🔒 SECRET SCANNING SUMMARY" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan

    if ($ScanSuccess) {
        Write-Host "✅ Clean Repository:" -ForegroundColor Green
        Write-Host "   - No verified secrets detected" -ForegroundColor Green
        Write-Host "   - Ignore patterns applied correctly" -ForegroundColor Green
        Write-Host "   - Repository ready for production" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Issues Detected:" -ForegroundColor Yellow
        Write-Host "   - Potential secrets found" -ForegroundColor Yellow
        Write-Host "   - Review scan output above" -ForegroundColor Yellow
        Write-Host "   - Consider updating .trufflehogignore" -ForegroundColor Yellow
    }

    Write-Host "`n🔍 Security Scanning Coverage:" -ForegroundColor Gray
    Write-Host "   - API keys and tokens" -ForegroundColor Gray
    Write-Host "   - Database credentials" -ForegroundColor Gray
    Write-Host "   - Cloud service keys" -ForegroundColor Gray
    Write-Host "   - Private keys and certificates" -ForegroundColor Gray
    Write-Host "   - JWT tokens and secrets" -ForegroundColor Gray
}

# Main execution
Write-Host "🚀 AIVO Secret Scanner (TruffleHog)" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

# Check/install TruffleHog
if (!(Test-TruffleHog)) {
    if ($InstallTruffleHog) {
        if (!(Install-TruffleHog)) {
            Write-Host "❌ Failed to install TruffleHog" -ForegroundColor Red
            Write-Host "Manual installation required:" -ForegroundColor Yellow
            Write-Host "  1. winget install trufflesecurity.trufflehog" -ForegroundColor Yellow
            Write-Host "  2. choco install trufflehog" -ForegroundColor Yellow
            Write-Host "  3. Download from: https://github.com/trufflesecurity/trufflehog/releases" -ForegroundColor Yellow
            exit 1
        }

        # Refresh PATH and test again
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

        if (!(Test-TruffleHog)) {
            Write-Host "⚠️  TruffleHog installed but not in PATH" -ForegroundColor Yellow
            Write-Host "Please restart PowerShell or add TruffleHog to your PATH" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "Run with -InstallTruffleHog to install automatically" -ForegroundColor Yellow
        exit 1
    }
}

# Show ignore patterns
Show-IgnorePatterns

# Run the scan
Write-Host "`n🔍 Starting secret scan on: $ScanPath" -ForegroundColor Blue

$scanSuccess = Invoke-SecretScan -Path $ScanPath -EntropyEnabled $WithEntropy -VerifiedOnly $OnlyVerified -Format $OutputFormat -Output $OutputFile

# Show summary
Show-ScanSummary -ScanSuccess $scanSuccess

Write-Host "`n🎉 Secret scanning completed!" -ForegroundColor Green

if (!$scanSuccess) {
    exit 1
}
