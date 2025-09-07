#!/usr/bin/env powershell

# PowerShell script to update all Dockerfiles to use Node 20.19 and fix casing issues
# Equivalent to the bash script provided

Write-Host "Starting Dockerfile updates..."

# Find all Dockerfile files excluding node_modules
$dockerfiles = Get-ChildItem -Recurse -Filter "Dockerfile" | Where-Object { 
    $_.FullName -notmatch "node_modules" 
}

$totalUpdated = 0

foreach ($dockerfile in $dockerfiles) {
    Write-Host "Processing $($dockerfile.FullName)"
    
    $content = Get-Content $dockerfile.FullName
    $updated = $false
    $newContent = @()
    
    foreach ($line in $content) {
        $newLine = $line
        
        # Update to specific Node version 20.19-alpine
        if ($line -match "FROM node:[0-9]+(\.[0-9]+)*(-alpine)?") {
            $newLine = $line -replace "FROM node:[0-9]+(\.[0-9]+)*(-alpine)?", "FROM node:20.19-alpine"
            $updated = $true
            Write-Host "  Updated Node version: $newLine" -ForegroundColor Green
        }
        
        # Fix the AS casing issue (lowercase 'as' to uppercase 'AS')
        if ($line -match "FROM .* as ") {
            $newLine = $line -replace " as ", " AS "
            $updated = $true
            Write-Host "  Fixed AS casing: $newLine" -ForegroundColor Green
        }
        
        $newContent += $newLine
    }
    
    if ($updated) {
        $newContent | Set-Content $dockerfile.FullName -Encoding UTF8
        Write-Host "  File updated!" -ForegroundColor Yellow
        $totalUpdated++
    } else {
        Write-Host "  No changes needed" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Dockerfile update complete!" -ForegroundColor Green
Write-Host "Total files processed: $($dockerfiles.Count)" -ForegroundColor Cyan
Write-Host "Total files updated: $totalUpdated" -ForegroundColor Yellow

if ($totalUpdated -gt 0) {
    Write-Host ""
    Write-Host "Remember to:" -ForegroundColor Blue
    Write-Host "   - Test your Docker builds" -ForegroundColor White
    Write-Host "   - Update any CI/CD pipelines if needed" -ForegroundColor White
    Write-Host "   - Commit these changes to version control" -ForegroundColor White
}
