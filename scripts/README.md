# AIVO Scripts Directory

This directory contains automation scripts for maintaining and securing the
AIVO monorepo infrastructure.

## Docker Security Scripts

### `docker-security-scan-fix.ps1` (Windows PowerShell)

Comprehensive Docker security scanning and fixing script for Windows.

**Usage:**

```powershell
# Run with default settings
.\scripts\docker-security-scan-fix.ps1

# Skip creating backup files
.\scripts\docker-security-scan-fix.ps1 -SkipBackups

# Run with verbose output
.\scripts\docker-security-scan-fix.ps1 -Verbose
```

**Features:**

- ✅ Docker Scout vulnerability scanning
- ✅ SBOM (Software Bill of Materials) generation
- ✅ Security recommendations
- ✅ Automatic Dockerfile fixes
- ✅ Docker Compose format updates
- ✅ Node.js version standardization

### `docker-security-scan-fix.sh` (Cross-platform Bash)

Cross-platform version of the security script for Linux/macOS/WSL.

**Usage:**

```bash
# Make executable and run
chmod +x scripts/docker-security-scan-fix.sh
./scripts/docker-security-scan-fix.sh
```

## Existing Docker Scripts

### `docker-improvements-summary.ps1`

Shows a summary of all Docker improvements completed in the monorepo.

### `update-dockerfiles.ps1`

Updates all Dockerfiles with latest Node.js versions and security improvements.

### `fix-npm-vulnerabilities.ps1`

Scans and fixes npm security vulnerabilities across all Node.js projects.

### `add-hadolint-ignore.ps1`

Adds hadolint ignore comments to Dockerfiles for known acceptable warnings.

## Prerequisites

### For Docker Scout Features:

- Docker Desktop 4.17.0 or later
- Docker Scout enabled (included in Docker Desktop 4.25.0+)
- Organization enrolled in Docker Scout (script will attempt to enroll)

### For General Docker Operations:

- Docker Desktop or Docker Engine
- PowerShell 5.1+ (for .ps1 scripts)
- Bash (for .sh scripts)

## Security Scanning Workflow

1. **Run the security scan script:**

   ```powershell
   .\scripts\docker-security-scan-fix.ps1
   ```

2. **Review generated files:**
   - `*-sbom.json` - Software Bill of Materials for each scanned image
   - Console output with vulnerability reports and recommendations

3. **Address critical vulnerabilities:**
   - Update base images
   - Update dependencies
   - Apply security patches

4. **Integrate into CI/CD:**
   - Use Docker Scout in GitHub Actions
   - Set up automated vulnerability scanning
   - Create security policies

## Common Docker Scout Commands

```bash
# Quick vulnerability overview
docker scout quickview

# Scan specific image
docker scout cves your-image:tag

# Generate SBOM
docker scout sbom your-image:tag

# Get security recommendations
docker scout recommendations your-image:tag

# Compare images
docker scout compare your-image:v1 your-image:v2
```

## Troubleshooting

### Docker Scout Not Available

- Update Docker Desktop to 4.17.0 or later
- Ensure Docker Scout is enabled in Docker Desktop settings

### Permission Errors

- Run PowerShell as Administrator (Windows)
- Use `sudo` for Docker commands (Linux/macOS)
- Check Docker daemon is running

### Image Not Found

- Build the image first: `docker build -t your-image .`
- Or scan existing images: `docker images` to list available images

## Integration with CI/CD

The scripts can be integrated into your CI/CD pipeline:

### GitHub Actions Example:

```yaml
- name: Run Docker Security Scan
  run: |
    chmod +x scripts/docker-security-scan-fix.sh
    ./scripts/docker-security-scan-fix.sh
```

### PowerShell in CI:

```yaml
- name: Run Docker Security Scan (Windows)
  shell: pwsh
  run: |
    .\scripts\docker-security-scan-fix.ps1 -SkipBackups
```
