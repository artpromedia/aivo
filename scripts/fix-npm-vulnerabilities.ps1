#!/usr/bin/env powershell

# PowerShell script to fix npm vulnerabilities across all services
# Equivalent to the bash script provided

Write-Host "Starting npm vulnerability fixes..." -ForegroundColor Blue

# Update npm to latest globally
Write-Host "Updating npm to latest version..." -ForegroundColor Yellow
npm install -g npm@latest

# Find all services with package.json
$services = Get-ChildItem -Path "services" -Directory | Where-Object {
    Test-Path (Join-Path $_.FullName "package.json")
}

$totalServicesFixed = 0

foreach ($service in $services) {
    $servicePath = $service.FullName
    $serviceName = $service.Name
    
    Write-Host "Fixing vulnerabilities in $serviceName" -ForegroundColor Cyan
    
    # Change to service directory
    Push-Location $servicePath
    
    try {
        # Update dependencies and fix vulnerabilities
        Write-Host "  Updating dependencies..." -ForegroundColor Gray
        npm update
        
        Write-Host "  Running npm audit fix..." -ForegroundColor Gray
        npm audit fix --force
        
        # Update lock file
        Write-Host "  Updating package-lock.json..." -ForegroundColor Gray
        npm install
        
        $totalServicesFixed++
        Write-Host "  ✓ $serviceName fixed!" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Error fixing $serviceName : $_" -ForegroundColor Red
    }
    finally {
        # Return to original directory
        Pop-Location
    }
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Blue
Write-Host "Vulnerability fixes complete!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Blue
Write-Host "Services processed: $($services.Count)" -ForegroundColor White
Write-Host "Services fixed: $totalServicesFixed" -ForegroundColor Yellow

if ($totalServicesFixed -gt 0) {
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Blue
    Write-Host "   - Test your applications to ensure they still work" -ForegroundColor White
    Write-Host "   - Review any changes to package-lock.json files" -ForegroundColor White
    Write-Host "   - Commit the updated lock files to version control" -ForegroundColor White
}
