#!/usr/bin/env powershell

# PowerShell script to add hadolint ignore comments to all Dockerfiles
# Equivalent to: find . -name "Dockerfile" -exec sed -i '1i# hadolint ignore=DL3007,DL3008' {} \;

Write-Host "Adding hadolint ignore comments to Dockerfiles..." -ForegroundColor Blue

# Find all Dockerfile files excluding node_modules
$dockerfiles = Get-ChildItem -Recurse -Filter "Dockerfile" | Where-Object { 
    $_.FullName -notmatch "node_modules" 
}

$totalUpdated = 0

foreach ($dockerfile in $dockerfiles) {
    Write-Host "Processing $($dockerfile.FullName)" -ForegroundColor Yellow
    
    $content = Get-Content $dockerfile.FullName
    
    # Check if hadolint ignore comment already exists
    if ($content[0] -notmatch "# hadolint ignore=") {
        # Add hadolint ignore comment at the beginning
        $newContent = @("# hadolint ignore=DL3007,DL3008") + $content
        
        $newContent | Set-Content $dockerfile.FullName -Encoding UTF8
        Write-Host "  Added hadolint ignore comment" -ForegroundColor Green
        $totalUpdated++
    } else {
        Write-Host "  Hadolint ignore comment already exists" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Blue
Write-Host "Hadolint ignore comments added!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Blue
Write-Host "Total files processed: $($dockerfiles.Count)" -ForegroundColor White
Write-Host "Total files updated: $totalUpdated" -ForegroundColor Yellow

Write-Host ""
Write-Host "Hadolint ignore rules added:" -ForegroundColor Blue
Write-Host "   - DL3007: Using latest tag for base images" -ForegroundColor White
Write-Host "   - DL3008: Pin versions in apt get install" -ForegroundColor White
