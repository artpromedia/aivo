#!/usr/bin/env pwsh
# Comprehensive VS Code cache reset script for persistent ESLint/TypeScript issues

Write-Host "=== VS Code Cache Reset Script ===" -ForegroundColor Green
Write-Host "This script will clear all VS Code caches to resolve phantom file issues." -ForegroundColor Yellow
Write-Host ""

# Step 1: Close VS Code if running
Write-Host "Step 1: Checking for running VS Code processes..." -ForegroundColor Cyan
$vscodeProcesses = Get-Process code -ErrorAction SilentlyContinue
if ($vscodeProcesses) {
    Write-Host "Found running VS Code processes. Please close VS Code manually before continuing." -ForegroundColor Red
    Write-Host "Press any key after closing VS Code to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} else {
    Write-Host "No VS Code processes found running." -ForegroundColor Green
}

# Step 2: Clear VS Code workspace storage
Write-Host "`nStep 2: Clearing VS Code workspace storage..." -ForegroundColor Cyan
$userProfile = $env:USERPROFILE
$vscodeData = @(
    "$userProfile\AppData\Roaming\Code\User\workspaceStorage",
    "$userProfile\AppData\Roaming\Code\CachedExtensions",
    "$userProfile\AppData\Roaming\Code\CachedExtensionVSIXs",
    "$userProfile\AppData\Roaming\Code\logs"
)

foreach ($path in $vscodeData) {
    if (Test-Path $path) {
        Write-Host "Removing: $path" -ForegroundColor Yellow
        try {
            Remove-Item $path -Recurse -Force
            Write-Host "Removed successfully" -ForegroundColor Green
        } catch {
            Write-Host "Failed to remove: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Path not found: $path" -ForegroundColor Gray
    }
}

# Step 3: Clear TypeScript cache
Write-Host "`nStep 3: Clearing TypeScript cache..." -ForegroundColor Cyan
$tscache = "$env:TEMP\typescript"
if (Test-Path $tscache) {
    Write-Host "Removing TypeScript cache: $tscache" -ForegroundColor Yellow
    try {
        Remove-Item $tscache -Recurse -Force
        Write-Host "TypeScript cache cleared" -ForegroundColor Green
    } catch {
        Write-Host "Failed to clear TypeScript cache: $_" -ForegroundColor Red
    }
} else {
    Write-Host "TypeScript cache not found" -ForegroundColor Gray
}

# Step 4: Clear ESLint cache
Write-Host "`nStep 4: Clearing ESLint cache..." -ForegroundColor Cyan
$eslintCache = ".eslintcache"
if (Test-Path $eslintCache) {
    Write-Host "Removing ESLint cache: $eslintCache" -ForegroundColor Yellow
    Remove-Item $eslintCache -Force
    Write-Host "ESLint cache cleared" -ForegroundColor Green
} else {
    Write-Host "ESLint cache not found" -ForegroundColor Gray
}

# Step 5: Clear node_modules and reinstall
Write-Host "`nStep 5: Clearing node_modules..." -ForegroundColor Cyan
if (Test-Path "node_modules") {
    Write-Host "Removing node_modules..." -ForegroundColor Yellow
    Remove-Item "node_modules" -Recurse -Force
    Write-Host "node_modules removed" -ForegroundColor Green
} else {
    Write-Host "node_modules not found" -ForegroundColor Gray
}

# Reinstall packages
Write-Host "Reinstalling packages..." -ForegroundColor Yellow
pnpm install
Write-Host "Packages reinstalled" -ForegroundColor Green

Write-Host "`n=== Cache Reset Complete ===" -ForegroundColor Green
Write-Host "Please restart VS Code and reopen the workspace." -ForegroundColor Yellow
Write-Host "The phantom .eslintrc.js TypeScript errors should now be resolved." -ForegroundColor Green
