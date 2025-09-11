# AIVO i18n Service 

**#S2B-09  Localization & Accessibility Gates**

Comprehensive internationalization service with WCAG 2.2 AA accessibility compliance, supporting African languages including Igbo, Yoruba, Hausa, Efik, Swahili, and Xhosa.

##  Features

- ** Multi-language Support**: Full i18n with African language priority
- ** WCAG 2.2 AA Compliance**: 98% accessibility compliance target
- ** CI Accessibility Gates**: Automated Axe/Pa11y/Lighthouse audits
- ** Translation Management**: RESTful API with bulk operations
- ** CLI Tools**: String extraction and locale management
- ** Fallback Logic**: Smart African language fallback chains

##  Architecture

```
services/i18n-svc/
 app/
    models/          # SQLAlchemy 2.0 models
    services/        # Business logic services  
    cli/            # Command-line tools
    main.py         # FastAPI application
    schemas.py      # Pydantic models
 .github/workflows/  # CI accessibility gates
 pyproject.toml     # Poetry configuration
```

##  Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- PostgreSQL (or SQLite for testing)

### Installation

```bash
cd services/i18n-svc
poetry install
```

### Database Setup

```bash
# Create PostgreSQL database
createdb i18n_db

# Set environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/i18n_db"
```

### Start Service

```bash
poetry run uvicorn app.main:app --reload
```

API Documentation: http://localhost:8000/docs

##  Supported African Languages

| Language | Code | Region | Fallback |
|----------|------|--------|----------|
| **Igbo** | `ig-NG` | Nigeria | `en-US` |
| **Yoruba** | `yo-NG` | Nigeria | `en-US` |
| **Hausa** | `ha-NG` | Nigeria | `en-US` |
| **Efik** | `efi-NG` | Nigeria | `en-US` |
| **Swahili** | `sw-KE`, `sw-TZ` | Kenya, Tanzania | `en-US` |
| **Xhosa** | `xh-ZA` | South Africa | `en-US` |

##  CLI Tools

### Extract Translatable Strings

```bash
# Extract from source code
poetry run python -m app.cli.i18n_cli extract --source ../.. --output locales/messages.pot

# Update locale files
poetry run python -m app.cli.i18n_cli update-locale --locale ig-NG

# Validate completeness
poetry run python -m app.cli.i18n_cli validate-locale --locale ig-NG

# Show statistics
poetry run python -m app.cli.i18n_cli stats
```

### Compile Translations

```bash
# Compile all locales to JSON
poetry run python -m app.cli.i18n_cli compile-translations

# Compile specific locale
poetry run python -m app.cli.i18n_cli compile-translations --locale ig-NG
```

##  API Endpoints

### Translations

```http
POST   /translations              # Create translation
GET    /translations              # List translations
GET    /translations/{id}         # Get translation
PUT    /translations/{id}         # Update translation
DELETE /translations/{id}         # Delete translation
POST   /translations/{id}/approve # Approve translation
```

### Locales

```http
POST /locales                     # Create locale config
GET  /locales                     # List locales
GET  /locales/{locale}/stats      # Get completion stats
```

### Accessibility

```http
POST /accessibility/audit/{id}           # Audit translation
POST /accessibility/audit/locale/{locale} # Bulk audit locale
GET  /accessibility/stats                # Get compliance stats
GET  /accessibility/audits               # Get audit history
```

### Bulk Operations

```http
POST /translations/bulk-import           # Import translations
GET  /translations/locale/{locale}/export # Export locale
GET  /translations/missing/{locale}     # Find missing translations
```

##  Accessibility Compliance

### WCAG 2.2 AA Requirements

- **Target**: 98% compliance rate
- **Automatic Audits**: Every 90 days
- **CI Gates**: Block deployment on failures
- **Tools**: Axe-core, Pa11y, Lighthouse

### Compliance Validation

```python
from app.services.accessibility_service import validate_wcag_compliance

result = validate_wcag_compliance({
    "value": "Welcome to our application",
    "locale": "en-US"
})

print(f"Score: {result['score']}%")
print(f"WCAG Level: {result['wcag_level']}")
```

##  CI/CD Accessibility Gates

The `.github/workflows/axe.yml` workflow runs:

1. **String Extraction**: Validates African language support
2. **Axe-core Audit**: WCAG 2.2 AA compliance check  
3. **Pa11y Audit**: Additional accessibility validation
4. **Lighthouse Audit**: 98% accessibility score requirement
5. **Translation Compliance**: African language fallback testing

### Workflow Triggers

- Push to `main`/`develop`
- Pull requests
- Weekly scheduled runs (Mondays 2 AM)

##  Development Workflow

### Code Quality

```bash
# Format code (short commands as required)
poetry run ruff format .

# Lint code  
poetry run ruff check .

# Type checking
poetry run mypy app/
```

### Testing

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Accessibility tests
poetry run pytest tests/test_accessibility.py
```

##  Key Features

### African Language Support

- **Native Fallback Logic**: Intelligent fallback chains for African languages
- **Cultural Context**: RTL support and locale-specific formatting
- **Compliance Tracking**: WCAG compliance per African language

### Accessibility Features

- **Readability Analysis**: Flesch score and grade level calculations
- **Screen Reader Optimization**: Proper punctuation validation
- **WCAG 2.2 AA Compliance**: Comprehensive validation rules
- **Automated Auditing**: Scheduled accessibility audits

### Developer Experience

- **CLI Tools**: Short commands for string extraction and management
- **Type Safety**: Full TypeScript-like typing with Pydantic
- **API Documentation**: Auto-generated OpenAPI docs
- **Hot Reload**: Development server with live reloading

##  Configuration

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/i18n_db
REDIS_URL=redis://localhost:6379/0
DEBUG=true
WCAG_TARGET_PERCENTAGE=98
```

### Poetry Scripts

```toml
[tool.poetry.scripts]
extract-strings = "app.cli.i18n_cli:extract"
update-locales = "app.cli.i18n_cli:update_locale"
a11y-audit = "app.cli.accessibility_cli:audit"
```

##  Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/african-locale-support`
3. Make changes with accessibility in mind
4. Run accessibility gates: `pytest tests/test_accessibility.py`
5. Submit pull request

All changes must pass the accessibility CI gates before merging.

##  License

MIT License - Supporting global accessibility and African language inclusion.

---

**feat(i18n+a11y): locales + ci accessibility gates** 
