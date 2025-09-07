#!/usr/bin/env powershell

# Script to restart ESLint and fix linting issues for Node.js email service

Write-Host "Fixing ESLint Configuration for Node.js Email Service..." -ForegroundColor Blue

# Change to the Node.js template directory
Set-Location "services\notification-svc\nodejs-email-template"

Write-Host ""
Write-Host "1. Cleaning up old configuration files..." -ForegroundColor Cyan
Remove-Item ".eslintrc.*" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "2. Installing/updating dependencies..." -ForegroundColor Cyan
if (Test-Path "package.json") {
    npm install --save-dev eslint@latest
} else {
    Write-Host "⚠️  package.json not found. Creating basic Node.js project..." -ForegroundColor Yellow
    npm init -y
    npm install --save-dev eslint@latest
}

Write-Host ""
Write-Host "3. Verifying ESLint configuration..." -ForegroundColor Cyan
if (Test-Path ".eslintrc.json") {
    Write-Host "✓ .eslintrc.json found" -ForegroundColor Green
} else {
    Write-Host "❌ .eslintrc.json missing" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "4. Running ESLint to check current status..." -ForegroundColor Cyan
npm run lint 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ No ESLint errors found" -ForegroundColor Green
} else {
    Write-Host "ℹ️  ESLint found some issues, attempting auto-fix..." -ForegroundColor Yellow
    npm run lint:fix 2>$null
}

Write-Host ""
Write-Host "5. Final verification..." -ForegroundColor Cyan
npm run lint 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All ESLint issues resolved" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some issues may need manual fixing" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Blue
Write-Host "ESLint configuration fixed!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Blue

Write-Host ""
Write-Host "VS Code actions needed:" -ForegroundColor Yellow
Write-Host "1. Restart VS Code or reload window (Ctrl+Shift+P -> 'Developer: Reload Window')" -ForegroundColor White
Write-Host "2. If issues persist: Ctrl+Shift+P -> 'ESLint: Restart ESLint Server'" -ForegroundColor White
Write-Host "3. If TypeScript errors persist: Ctrl+Shift+P -> 'TypeScript: Restart TS Server'" -ForegroundColor White

# Return to original directory
Set-Location "..\..\..\"
