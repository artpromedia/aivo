# Stage-0 Verification Script (Simple PowerShell)
Write-Host "========================================"
Write-Host "Stage-0 Completion Verification" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host ""

$checks = 0
$passed = 0

# Function to check if file exists
function Test-File($path, $name) {
    $script:checks++
    if (Test-Path $path) {
        Write-Host "✅ $name exists ($path)" -ForegroundColor Green
        $script:passed++
        return $true
    } else {
        Write-Host "❌ $name missing ($path)" -ForegroundColor Red
        return $false
    }
}

# Function to check if command exists
function Test-Command($cmd, $name) {
    $script:checks++
    try {
        $null = Get-Command $cmd -ErrorAction Stop
        Write-Host "✅ $name is available" -ForegroundColor Green
        $script:passed++
        return $true
    } catch {
        Write-Host "❌ $name is not available" -ForegroundColor Red
        return $false
    }
}

Write-Host "Checking basic tools..."
Test-Command "node" "Node.js"
Test-Command "pnpm" "pnpm"
Test-Command "python" "Python"
Test-Command "git" "Git"
Test-Command "docker" "Docker"

Write-Host ""
Write-Host "Checking project structure..."
Test-File "package.json" "Root package.json"
Test-File "pyproject.toml" "Python project config"
Test-File "Makefile" "Build system Makefile"
Test-File ".vscode/settings.json" "VS Code settings"

Write-Host ""
Write-Host "Checking Kong Gateway..."
Test-File "apps/gateway/kong.yml" "Kong config"
Test-File "apps/gateway/README.md" "Gateway docs"

Write-Host ""
Write-Host "Checking Hello Service..."
Test-File "services/hello-svc/pyproject.toml" "Hello service config"
Test-File "services/hello-svc/app/main.py" "Hello service app"
Test-File "services/hello-svc/tests/test_ping.py" "Hello service tests"

Write-Host ""
Write-Host "Checking CI workflows..."
Test-File ".github/workflows/ci.yml" "Main CI workflow"
Test-File ".github/workflows/security.yml" "Security workflow"
Test-File ".github/workflows/dep-guard.yml" "Dependency guard"

Write-Host ""
Write-Host "Checking scripts..."
Test-File "scripts/check-npm-deprecations.mjs" "NPM deprecation checker"
Test-File "scripts/ensure-eslint9.mjs" "ESLint v9 enforcer"
Test-File "scripts/verify-stage0.ps1" "Stage-0 verifier"

Write-Host ""
Write-Host "========================================"
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host "Total checks: $checks"
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $($checks - $passed)" -ForegroundColor Red

if ($passed -eq $checks) {
    Write-Host ""
    Write-Host "🎉 Stage-0 verification PASSED!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "💥 Stage-0 verification FAILED!" -ForegroundColor Red
    exit 1
}
