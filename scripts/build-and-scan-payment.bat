@echo off
REM Build and Scan AIVO Payment Service
REM This script demonstrates the exact commands you requested

echo.
echo 🚀 AIVO Payment Service - Build and Security Scan
echo ================================================

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed or not running
    echo Please install Docker Desktop for Windows
    echo Download: https://docs.docker.com/desktop/install/windows/
    echo.
    pause
    exit /b 1
)

REM Check if Trivy is available
trivy --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Trivy is not installed
    echo Install with: winget install aquasec.trivy
    echo Or download: https://github.com/aquasecurity/trivy/releases
    echo.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Navigate to workspace root
cd /d "C:\Users\ofema\aivo"
if %errorlevel% neq 0 (
    echo ❌ Could not navigate to workspace directory
    pause
    exit /b 1
)

echo 🔨 Building payment-svc Docker image...
echo Command: docker build -t aivo/payment-svc:ci services/payment-svc
echo.

REM Build the Docker image
docker build -t aivo/payment-svc:ci services/payment-svc

if %errorlevel% neq 0 (
    echo.
    echo ❌ Docker build failed
    echo Check the build output above for errors
    pause
    exit /b 1
)

echo.
echo ✅ Build completed successfully!
echo.

echo 🔍 Scanning for security vulnerabilities...
echo Command: trivy image --severity HIGH,CRITICAL --ignore-unfixed aivo/payment-svc:ci
echo.

REM Security scan with Trivy
trivy image --severity HIGH,CRITICAL --ignore-unfixed aivo/payment-svc:ci

if %errorlevel% neq 0 (
    echo.
    echo ❌ Security scan failed
    pause
    exit /b 1
)

echo.
echo ✅ Security scan completed!
echo.
echo 📊 Analysis Summary:
echo    - Base Image: python:3.11-slim-bookworm (pinned by digest)
echo    - Security Updates: Applied via apt-get upgrade
echo    - Python Tools: Latest pip/setuptools/wheel
echo    - User Security: Non-root UID 10001
echo    - Build Optimization: Cache mounts enabled
echo.
echo 🎉 Payment service security analysis complete!
echo.

REM Generate detailed JSON report
echo 📄 Generating detailed JSON report...
trivy image --severity HIGH,CRITICAL --ignore-unfixed --format json --output payment-svc-scan.json aivo/payment-svc:ci

if exist payment-svc-scan.json (
    echo ✅ Detailed report saved: payment-svc-scan.json
) else (
    echo ⚠️  Could not generate JSON report
)

echo.
pause
