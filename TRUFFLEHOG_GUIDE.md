# TruffleHog Secret Scanning Guide

## 🔍 TruffleHog Installation & Usage

### Installation Options

#### Option 1: winget (Recommended)
```powershell
winget install trufflesecurity.trufflehog
```

#### Option 2: Chocolatey
```powershell
choco install trufflehog
```

#### Option 3: Direct Download
```powershell
# Download latest release
$url = "https://github.com/trufflesecurity/trufflehog/releases/latest/download/trufflehog_windows_amd64.exe"
Invoke-WebRequest -Uri $url -OutFile "$env:USERPROFILE\trufflehog.exe"

# Add to PATH or move to a directory in PATH
```

### Your Requested Command

```bash
# Scan filesystem with entropy detection disabled
trufflehog filesystem --entropy=False .
```

### Alternative TruffleHog Commands

#### Basic Scans
```bash
# Scan with verified secrets only
trufflehog filesystem --only-verified .

# Scan with entropy detection enabled
trufflehog filesystem .

# Scan specific directory
trufflehog filesystem ./services/

# Scan with JSON output
trufflehog filesystem --entropy=False --format=json .
```

#### Advanced Scans
```bash
# Scan with custom output file
trufflehog filesystem --entropy=False --output=secrets-report.json --format=json .

# Scan only verified secrets with JSON output
trufflehog filesystem --only-verified --format=json --output=verified-secrets.json .

# Scan with specific detectors
trufflehog filesystem --detectors=aws,github,stripe .
```

## 🔒 Expected Results with .trufflehogignore

With our `.trufflehogignore` configuration, the following should be ignored:

### Ignored Paths:
- `^docs/` - Documentation with example keys
- `^tests/fixtures/` - Test fixtures with fake credentials  
- `^apps/admin/public/` - Public admin assets
- `.*\.sample$` - Sample configuration files
- `.*_example\..*$` - Example files
- `.*-fixture\..*$` - Fixture files

### Typical Scan Output (Clean Repository):
```
🔍 TruffleHog Filesystem Scan
============================
Found verified result 🐷🔑

Detector Type: AWS
Decoder Type: PLAIN
Raw result: AKIA...
File: config/production.env
Email: dev@aivo.com
Repository: file:///C:/Users/ofema/aivo
Timestamp: 2025-09-12T...
Line: 15
Commit: abc123...

🐷  DETECTION SUMMARY 
====================
Found 0 verified secrets
Found 3 unverified secrets (ignored due to --only-verified)
```

### Common Secret Types Detected:
- **AWS Keys**: AKIA..., aws_access_key_id
- **GitHub Tokens**: ghp_..., github_pat_...
- **Stripe Keys**: sk_live_..., pk_live_...
- **Database URLs**: postgresql://user:pass@host
- **JWT Secrets**: Long random strings
- **API Keys**: Various service-specific patterns

## 🛠️ Integration with AIVO Security

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run TruffleHog
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: main
    head: HEAD
    extra_args: --entropy=false --only-verified
```

### Pre-commit Hook
```bash
# Add to .pre-commit-config.yaml
repos:
  - repo: https://github.com/trufflesecurity/trufflehog
    rev: main
    hooks:
      - id: trufflehog
        args: ['--entropy=False', '--only-verified']
```

## 🔍 Manual Secret Pattern Check

If TruffleHog is not available, you can use basic pattern matching:

### PowerShell Secret Search
```powershell
# Search for common secret patterns
Get-ChildItem -Recurse -File | Select-String -Pattern "AKIA[0-9A-Z]{16}" | Select-Object Filename, LineNumber, Line
Get-ChildItem -Recurse -File | Select-String -Pattern "sk_live_[0-9A-Za-z]{24}" | Select-Object Filename, LineNumber, Line
Get-ChildItem -Recurse -File | Select-String -Pattern "ghp_[0-9A-Za-z]{36}" | Select-Object Filename, LineNumber, Line
```

### Git Secret History Scan
```bash
# Scan git history for secrets
git log --all --grep="password\|secret\|key" --oneline
git log -p --all -S "AKIA" --source --all
```

## 📊 Security Assessment

### Current AIVO Security Posture:
- ✅ `.trufflehogignore` configured to reduce false positives
- ✅ Docker secrets managed via environment variables
- ✅ Development configs use `.env` files (gitignored)
- ✅ Production secrets externalized to secure vaults

### Recommendations:
1. **Install TruffleHog**: Add to developer toolchain
2. **CI/CD Integration**: Run on every commit/PR
3. **Regular Scans**: Weekly secret audits
4. **Secret Rotation**: Regular key rotation for any detected secrets
5. **Vault Integration**: Use HashiCorp Vault or similar for production

## 🚀 Automated Scanning

Use our PowerShell script for comprehensive scanning:

```powershell
# Install and run TruffleHog
.\scripts\secret-scan.ps1 -InstallTruffleHog

# Run scan with current settings (entropy=False)
.\scripts\secret-scan.ps1 -ScanPath . -WithEntropy:$false

# Verified secrets only with JSON output
.\scripts\secret-scan.ps1 -OnlyVerified -OutputFormat json -OutputFile secrets-report.json
```

---

**Status**: Ready for TruffleHog secret scanning with comprehensive ignore patterns and automation support.
