# Security Audit Guide for AIVO Python Services

## 🔍 pip-audit Security Scanning

### Prerequisites

```bash
# Install security audit tools
pip install pip-audit safety
```

### Payment Service Audit Commands

#### Option 1 - Direct audit (pip-based service)

```bash
# Navigate to workspace
cd C:\Users\ofema\aivo

# Run pip-audit on requirements.txt
pip-audit -r services/payment-svc/requirements.txt

# Generate detailed JSON report
pip-audit -r services/payment-svc/requirements.txt --format=json --output=payment-svc-audit.json
```

#### Option 2 - Poetry export + audit (if using Poetry)

```bash
# If the service used Poetry (it doesn't, but for reference)
cd services/payment-svc
poetry export -f requirements.txt -o requirements.txt --without-hashes
pip-audit -r requirements.txt
```

### Safety Alternative

```bash
# Alternative security scanner
safety check -r services/payment-svc/requirements.txt
```

## 📋 Current Service Status

### Services Ready for Audit

1. **payment-svc** (pip-based)

   ```bash
   pip-audit -r services/payment-svc/requirements.txt
   ```

2. **auth-svc** (pip-based)

   ```bash
   pip-audit -r services/auth-svc/requirements.txt
   ```

3. **notification-svc** (pip-based)

   ```bash
   pip-audit -r services/notification-svc/requirements.txt
   ```

4. **user-svc** (pip-based)

   ```bash
   pip-audit -r services/user-svc/requirements.txt
   ```

5. **analytics-svc** (pip-based)

   ```bash
   pip-audit -r services/analytics-svc/requirements.txt
   ```

6. **billing-svc** (pip-based)

   ```bash
   pip-audit -r services/billing-svc/requirements.txt
   ```

### Current Dependencies (services/payment-svc/requirements.txt)

```text
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-decouple==3.8
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

### Security Considerations

- **FastAPI**: Generally secure, regularly updated
- **uvicorn**: ASGI server with good security track record
- **SQLAlchemy**: Major ORM with active security maintenance
- **psycopg2-binary**: PostgreSQL adapter, generally secure
- **python-jose**: JWT handling library - check for updates
- **passlib**: Password hashing library - well maintained
- **pydantic**: Data validation - excellent security features

### Best Case Scenario (With Security Hardening)

```text
✅ All dependencies up-to-date
✅ No known vulnerabilities
✅ Strong authentication mechanisms
✅ Proper input validation
✅ Secure database connections
✅ Rate limiting implemented
✅ HTTPS enforcement
✅ Security headers configured
```

### Potential Issues (Before Hardening)

```text
⚠️  Outdated dependencies
⚠️  Missing security headers
⚠️  No rate limiting
⚠️  Weak JWT configuration
⚠️  Missing input sanitization
⚠️  No request logging
⚠️  Insecure CORS settings
```

## 🛡️ Security Hardening Steps

### 1. Update Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update specific packages
pip install --upgrade fastapi uvicorn sqlalchemy
```

### 2. Add Security Headers

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### 3. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 4. Input Validation

```python
from pydantic import BaseModel, validator
from typing import Optional

class PaymentRequest(BaseModel):
    amount: float
    currency: str
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
```

## 📊 Audit Report Template

### Executive Summary

- **Total Services Audited**: X
- **High Severity Issues**: X
- **Medium Severity Issues**: X
- **Low Severity Issues**: X
- **Overall Risk Level**: [LOW/MEDIUM/HIGH]

### Detailed Findings

#### Service: payment-svc

**Dependencies Scanned**: X packages

**Vulnerabilities Found**:

1. **Package**: example-package
   - **Severity**: High
   - **Description**: SQL injection vulnerability
   - **Affected Versions**: < 2.1.0
   - **Fix**: Upgrade to >= 2.1.0

### Recommendations

1. **Immediate Actions**:
   - Update critical dependencies
   - Apply security patches

2. **Short-term Improvements**:
   - Implement rate limiting
   - Add security headers

3. **Long-term Strategy**:
   - Automated security scanning
   - Regular dependency updates

## 🔧 Automation Scripts

### Daily Security Check

```bash
#!/bin/bash
# daily-security-check.sh

echo "🔍 Running daily security audit..."

# Check all services
for service in payment-svc auth-svc user-svc notification-svc; do
    echo "Auditing $service..."
    pip-audit -r services/$service/requirements.txt --format=json --output=reports/$service-audit.json
done

echo "✅ Security audit complete"
```

### Weekly Dependency Update

```bash
#!/bin/bash
# weekly-update.sh

echo "📦 Checking for dependency updates..."

# Generate update report
pip list --outdated > reports/outdated-packages.txt

echo "✅ Update check complete"
```

## 📚 Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Guidelines](https://python.org/dev/security/)
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)

## 🚨 Emergency Response

### If Critical Vulnerability Found

1. **Immediate**: Stop affected services
2. **Assess**: Determine impact scope
3. **Patch**: Apply security updates
4. **Test**: Verify fix in staging
5. **Deploy**: Update production
6. **Monitor**: Watch for issues
7. **Document**: Record incident details
