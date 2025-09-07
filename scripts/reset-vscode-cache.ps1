#!/usr/bin/env powershell

# Script to completely reset VS Code TypeScript and ESLint for Node.js project

Write-Host "Resetting VS Code Language Servers and Cache..." -ForegroundColor Blue

# Save current directory
$originalDir = Get-Location

try {
    # Change to the Node.js template directory
    Set-Location "services\notification-svc\nodejs-email-template"

    Write-Host ""
    Write-Host "1. Cleaning up phantom files..." -ForegroundColor Cyan
    
    # Remove any remaining eslintrc files with different extensions
    Get-ChildItem -Filter ".eslintrc*" -Force | Remove-Item -Force -ErrorAction SilentlyContinue
    
    # Remove VS Code workspace cache if it exists
    if (Test-Path "$env:APPDATA\Code\User\workspaceStorage") {
        Write-Host "   Clearing VS Code workspace cache..." -ForegroundColor Gray
        Get-ChildItem "$env:APPDATA\Code\User\workspaceStorage" -Recurse | 
            Where-Object { $_.FullName -like "*monorepo*" } | 
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "2. Recreating clean configuration..." -ForegroundColor Cyan
    
    # Create a fresh .eslintrc.json
    $eslintConfig = @{
        env = @{
            node = $true
            es2021 = $true
            commonjs = $true
        }
        extends = @("eslint:recommended")
        parserOptions = @{
            ecmaVersion = 12
            sourceType = "commonjs"
        }
        rules = @{
            "no-console" = "off"
            "no-process-exit" = "off"
            "no-unused-vars" = @("error", @{ argsIgnorePattern = "^_" })
        }
        globals = @{
            Buffer = "readonly"
            global = "readonly"
            __dirname = "readonly"
            __filename = "readonly"
        }
    }
    
    $eslintConfig | ConvertTo-Json -Depth 4 | Set-Content ".eslintrc.json" -Encoding UTF8

    Write-Host ""
    Write-Host "3. Creating TypeScript exclusion config..." -ForegroundColor Cyan
    
    # Create jsconfig.json to exclude config files from TypeScript
    $jsConfig = @{
        compilerOptions = @{
            target = "ES2020"
            module = "commonjs"
            allowJs = $true
            skipLibCheck = $true
            strict = $false
            esModuleInterop = $true
            moduleResolution = "node"
        }
        include = @("**/*.js")
        exclude = @(
            "node_modules"
            ".eslintrc.*"
            "*.config.*"
            ".vscode"
        )
    }
    
    $jsConfig | ConvertTo-Json -Depth 3 | Set-Content "jsconfig.json" -Encoding UTF8

    Write-Host ""
    Write-Host "4. Verifying configuration..." -ForegroundColor Cyan
    
    if (Test-Path ".eslintrc.json") {
        $eslintContent = Get-Content ".eslintrc.json" -Raw
        if ($eslintContent.Trim() -ne "") {
            Write-Host "   ✓ .eslintrc.json created successfully" -ForegroundColor Green
        } else {
            Write-Host "   ❌ .eslintrc.json is empty" -ForegroundColor Red
        }
    } else {
        Write-Host "   ❌ .eslintrc.json not found" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Blue
    Write-Host "Configuration Reset Complete!" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Blue

    Write-Host ""
    Write-Host "CRITICAL: You must now restart VS Code completely:" -ForegroundColor Red
    Write-Host "1. Close VS Code entirely (File -> Exit)" -ForegroundColor Yellow
    Write-Host "2. Wait 5 seconds" -ForegroundColor Yellow
    Write-Host "3. Reopen VS Code and your workspace" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "If errors persist after restart:" -ForegroundColor Yellow
    Write-Host "• Ctrl+Shift+P -> 'Developer: Reload Window'" -ForegroundColor White
    Write-Host "• Ctrl+Shift+P -> 'TypeScript: Restart TS Server'" -ForegroundColor White
    Write-Host "• Ctrl+Shift+P -> 'ESLint: Restart ESLint Server'" -ForegroundColor White

} finally {
    # Return to original directory
    Set-Location $originalDir
}
