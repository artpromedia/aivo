# S2B-14 Stage-2B Verifier

End-to-end smoke testing across communications, compliance, accessibility, gateway, and RAI.

## Overview

The Stage-2B Verifier performs comprehensive end-to-end testing of the AIVO educational AI infrastructure, ensuring all critical systems are functioning correctly and meet compliance requirements.

## Test Flow

```
roster sync  lessons/ingest/search  chat (parent toggle)  evidence attach  
HLS playback  compliance export  Looker schedule  bias audit dry-run  Axe CI
```

## Features

###  **Comprehensive Testing**
- **Roster Sync**: Student/parent/teacher data synchronization
- **Lesson Management**: Content upload, indexing, and search
- **Communication**: Real-time chat with parent notification controls
- **Evidence Processing**: File upload and attachment handling
- **Media Streaming**: HLS video playback verification
- **Compliance Export**: FERPA/GDPR data export validation
- **Analytics**: Looker dashboard generation and scheduling
- **Responsible AI**: Bias audit and fairness assessment
- **Accessibility**: Axe CI compliance verification
- **Code Quality**: Python lint hygiene checks

###  **Compliance Verification**
-  FERPA compliance validation
-  GDPR data protection verification
-  Accessibility standards (WCAG 2.1)
-  AI bias and fairness auditing
-  Educational equity assessment

###  **Educational Focus**
- Student data privacy protection
- Parent communication controls
- Teacher dashboard functionality
- Learning content management
- Performance analytics
- Special needs accommodation

## Usage

### Prerequisites
```bash
# Install Node.js dependencies
npm install

# Install Python dependencies (if running Python services)
pip install ruff

# Install Axe CLI for accessibility testing
npm install -g @axe-core/cli
```

### Running the Verifier
```bash
# Run full verification suite
npm run verify

# Run with development watching
npm run verify:dev

# Run only lint checks
npm run lint
```

### Manual Execution
```bash
# Direct TypeScript execution
tsx verify-stage2b.ts

# With specific environment
NODE_ENV=staging tsx verify-stage2b.ts
```

## Configuration

The verifier supports configuration through environment variables:

```bash
# Service endpoints
GATEWAY_URL=http://localhost:8080
ROSTER_URL=http://localhost:8001
LESSONS_URL=http://localhost:8002
CHAT_URL=http://localhost:8003
EVIDENCE_URL=http://localhost:8004
HLS_URL=http://localhost:8005
COMPLIANCE_URL=http://localhost:8006
LOOKER_URL=http://localhost:8007
RAI_URL=http://localhost:8008

# Test configuration
TEST_STUDENT_ID=test-student-12345
TEST_PARENT_ID=test-parent-67890
TEST_TEACHER_ID=test-teacher-54321

# Timeout settings
SERVICE_TIMEOUT=5000
WEBSOCKET_TIMEOUT=3000
HLS_TIMEOUT=10000
EXPORT_TIMEOUT=15000
```

## Test Results

### Report Structure
```json
{
  "timestamp": "2025-09-11T18:30:00.000Z",
  "environment": "development",
  "totalTests": 10,
  "passed": 8,
  "failed": 1,
  "skipped": 1,
  "duration": 45230,
  "compliance": {
    "ferpa": true,
    "gdpr": true,
    "accessibility": true,
    "bias_audit": true
  },
  "results": [...]
}
```

### Compliance Status
- **FERPA**: Student data privacy compliance
- **GDPR**: European data protection compliance  
- **Accessibility**: WCAG 2.1 AA compliance
- **Bias Audit**: AI fairness and equity assessment

## Integration

### CI/CD Pipeline
```yaml
# .github/workflows/stage2b-verify.yml
name: Stage-2B Verification
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd scripts
          npm install
      - name: Run verification
        run: |
          cd scripts
          npm run verify
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: verification-report
          path: scripts/verification-report.json
```

### Pre-deployment Check
```bash
# Add to deployment pipeline
cd scripts && npm run verify || exit 1
```

## Educational Compliance

### FERPA Compliance
- Student record protection
- Parental consent management
- Educational purpose validation
- Access logging and auditing

### GDPR Compliance
- Data minimization principles
- Consent management
- Right to erasure
- Cross-border data transfer controls

### Accessibility Standards
- WCAG 2.1 AA compliance
- Screen reader compatibility
- Keyboard navigation support
- Color contrast validation
- Alternative text verification

### AI Ethics and Bias Auditing
- Demographic parity assessment
- Equal opportunity validation
- Educational equity measurement
- Protected attribute testing
- Stakeholder impact analysis

## Troubleshooting

### Common Issues

**Service Connection Errors**
```bash
# Check if services are running
curl http://localhost:8080/health

# Start required services
docker-compose up -d
```

**WebSocket Connection Failures**
```bash
# Verify WebSocket endpoints
wscat -c ws://localhost:8003/ws
```

**Accessibility Test Failures**
```bash
# Install Axe CLI if missing
npm install -g @axe-core/cli

# Run manual accessibility check
axe http://localhost:8080 --timeout 10000
```

**Python Lint Errors**
```bash
# Fix formatting issues
ruff format .

# Fix linting issues
ruff check . --fix
```

### Debug Mode
```bash
# Enable verbose logging
DEBUG=* tsx verify-stage2b.ts

# Test specific components
tsx verify-stage2b.ts --test=bias_audit
```

## Contributing

### Adding New Tests
1. Implement test method in `Stage2BVerifier` class
2. Add test to the `tests` array in `runVerification()`
3. Update compliance validation logic
4. Add configuration options if needed
5. Update documentation

### Test Guidelines
- Each test should be independent and atomic
- Use appropriate timeouts for network operations
- Include comprehensive error handling
- Validate both success and failure scenarios
- Document expected compliance outcomes

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions:
- **Documentation**: https://docs.aivo.education/verification
- **Issues**: https://github.com/aivo-education/aivo/issues
- **Email**: support@aivo.education
