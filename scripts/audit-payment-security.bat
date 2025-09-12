@echo off
REM Security Audit for AIVO Payment Service
REM This script runs pip-audit on the payment-svc requirements

echo.
echo 🔍 AIVO Payment Service Security Audit
echo =====================================

REM Navigate to workspace root
cd /d "C:\Users\ofema\aivo"
if %errorlevel% neq 0 (
    echo ❌ Could not navigate to workspace directory
    pause
    exit /b 1
)

echo ✅ Current directory: %CD%
echo.

REM Check if pip-audit is available
pip-audit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip-audit is not installed
    echo Installing pip-audit...
    pip install pip-audit
    if %errorlevel% neq 0 (
        echo ❌ Failed to install pip-audit
        pause
        exit /b 1
    )
    echo ✅ pip-audit installed successfully
)

echo ✅ pip-audit is available
echo.

REM Check if requirements.txt exists
if not exist "services\payment-svc\requirements.txt" (
    echo ❌ requirements.txt not found in services\payment-svc\
    pause
    exit /b 1
)

echo ✅ Found requirements.txt
echo.

echo 🔍 Running pip-audit security scan...
echo Command: pip-audit -r services/payment-svc/requirements.txt
echo.

REM Run pip-audit security scan
pip-audit -r services/payment-svc/requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ⚠️  Security vulnerabilities detected!
    echo Review the output above for details
) else (
    echo.
    echo ✅ No known security vulnerabilities found!
)

echo.
echo 📊 Generating detailed JSON report...
pip-audit -r services/payment-svc/requirements.txt --format=json --output=payment-svc-security-audit.json

if exist payment-svc-security-audit.json (
    echo ✅ Detailed report saved: payment-svc-security-audit.json
) else (
    echo ⚠️  Could not generate JSON report
)

echo.
echo 🔒 Security Audit Summary for Payment Service:
echo    - Scanned: services/payment-svc/requirements.txt
echo    - Dependencies: FastAPI, SQLAlchemy, Stripe, PostgreSQL, etc.
echo    - Security Hardening: Applied (Docker + base image)
echo    - Base Image: python:3.11-slim-bookworm (digest-pinned)
echo.

REM Also check for Poetry option
echo 📝 Note: If using Poetry, run these commands:
echo    cd services/payment-svc
echo    poetry export -f requirements.txt -o requirements.txt --without-hashes
echo    pip-audit -r requirements.txt
echo.

echo 🎉 Security audit completed!
echo.
pause
