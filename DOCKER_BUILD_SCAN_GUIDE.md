# Docker Build and Security Scan Instructions

## Prerequisites
1. **Docker Desktop**: Install Docker Desktop for Windows
2. **Trivy**: Install Trivy security scanner
   ```powershell
   # Install via winget
   winget install aquasec.trivy
   
   # Or download from GitHub releases
   # https://github.com/aquasecurity/trivy/releases
   ```

## Build and Scan Commands

### 1. Build the Payment Service
```bash
# Navigate to workspace root
cd C:\Users\ofema\aivo

# Build the Docker image
docker build -t aivo/payment-svc:ci services/payment-svc
```

### 2. Security Scan with Trivy
```bash
# Scan for HIGH and CRITICAL vulnerabilities only
trivy image --severity HIGH,CRITICAL --ignore-unfixed aivo/payment-svc:ci

# More detailed scan with output formats
trivy image --severity HIGH,CRITICAL --ignore-unfixed --format table aivo/payment-svc:ci

# Generate JSON report
trivy image --severity HIGH,CRITICAL --ignore-unfixed --format json --output payment-svc-scan.json aivo/payment-svc:ci
```

## Expected Security Improvements

With our security hardening, you should see:

### ✅ Reduced Vulnerabilities
- **Base Image**: Pinned `python:3.11-slim-bookworm@sha256:...` reduces floating tag risks
- **Security Updates**: `apt-get upgrade -y` applies latest patches
- **Updated Tools**: Latest pip/setuptools/wheel versions fix known CVEs

### ✅ Best Practices Applied
- **Non-root User**: Runs as UID 10001 (not root)
- **Fixed Dependencies**: Pinned base image prevents supply chain attacks
- **Optimized Layers**: Cache mounts improve build performance

### 🔍 What Trivy Will Check
1. **OS Vulnerabilities**: Debian package CVEs
2. **Python Package CVEs**: pip package vulnerabilities
3. **Application Dependencies**: requirements.txt security issues
4. **Configuration Issues**: Dockerfile security best practices

## Sample Expected Output

```
aivo/payment-svc:ci (debian 12.1)
==========================================
Total: 0 (HIGH: 0, CRITICAL: 0)

Python (python-pkg)
===================
Total: 0 (HIGH: 0, CRITICAL: 0)
```

## Alternative Services to Test

If you want to test the security scanning with different services:

```bash
# Build and scan other hardened services
docker build -t aivo/search-svc:ci services/search-svc
trivy image --severity HIGH,CRITICAL --ignore-unfixed aivo/search-svc:ci

docker build -t aivo/notification-svc:ci services/notification-svc  
trivy image --severity HIGH,CRITICAL --ignore-unfixed aivo/notification-svc:ci

docker build -t aivo/ink-svc:ci services/ink-svc
trivy image --severity HIGH,CRITICAL --ignore-unfixed aivo/ink-svc:ci
```

## Batch Scanning Script

```powershell
# Build and scan all hardened services
$services = @(
    "payment-svc",
    "search-svc", 
    "notification-svc",
    "ink-svc",
    "learner-svc",
    "event-collector-svc"
)

foreach ($service in $services) {
    Write-Host "Building and scanning $service..." -ForegroundColor Green
    
    # Build
    docker build -t "aivo/${service}:ci" "services/$service"
    
    # Scan
    trivy image --severity HIGH,CRITICAL --ignore-unfixed "aivo/${service}:ci"
    
    Write-Host "Completed $service`n" -ForegroundColor Blue
}
```

## Security Comparison

To see the security improvement, you could also scan a non-hardened image:

```bash
# Build original (before hardening) - if you have a backup
docker build -t aivo/payment-svc:original -f services/payment-svc/Dockerfile.original services/payment-svc

# Compare scan results
trivy image --severity HIGH,CRITICAL aivo/payment-svc:original
trivy image --severity HIGH,CRITICAL --ignore-unfixed aivo/payment-svc:ci
```
