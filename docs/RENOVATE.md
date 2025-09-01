# Renovate Configuration

This project uses [Renovate](https://renovatebot.com/) for automated dependency updates with strict safety controls.

## Features

### 🔒 ESLint v9 Protection

- **Locked to ESLint 9.x**: Prevents downgrades to ESLint v8
- **TypeScript ESLint compatibility**: Ensures plugins support ESLint v9
- **Plugin compatibility**: Validates ESLint plugin versions

### 🛡️ Deprecated Package Prevention

- **Automatic detection**: Rejects updates to deprecated packages
- **CI validation**: Every Renovate PR is validated for deprecated dependencies
- **Safe updates only**: Only allows updates to maintained packages

### ⚡ Smart Update Strategy

- **Semantic commits**: Follows conventional commit format
- **Scheduled updates**: Runs after 2 AM on Sundays
- **Rate limiting**: Maximum 2 PRs per hour, 5 concurrent PRs
- **Vulnerability alerts**: Immediate updates for security issues

## Configuration Files

- `renovate.json` - Main Renovate configuration
- `.github/workflows/renovate-validation.yml` - Validation workflow
- `scripts/validate-renovate-update.mjs` - Custom validation script

## Package Rules

### ESLint Ecosystem

```json
{
  "matchPackagePatterns": ["^eslint$", "^@eslint/js$"],
  "allowedVersions": ">=9 <10"
}
```

### TypeScript ESLint

```json
{
  "matchPackagePatterns": ["^@typescript-eslint/"],
  "allowedVersions": ">=8.0.0"
}
```

### ESLint Plugins

```json
{
  "matchPackagePatterns": ["^eslint-plugin-"],
  "allowedVersions": ">=2.0.0"
}
```

## Validation Process

Every Renovate PR goes through:

1. **ESLint Version Check**: Ensures ESLint >= 9.0.0
2. **Deprecated Package Check**: Runs `check-npm-deprecations.mjs`
3. **Compatibility Check**: Validates TypeScript ESLint plugin versions
4. **Lint Test**: Ensures the codebase still passes linting
5. **Package Integrity**: Verifies `pnpm install` works

## Manual Testing

Test Renovate updates locally:

```bash
# Run full validation
pnpm run renovate:validate

# Or run individual checks
node scripts/ensure-eslint9.mjs
node scripts/check-npm-deprecations.mjs
pnpm run lint
```

## Schedule

- **Regular updates**: Sundays after 2 AM
- **Lock file maintenance**: Mondays before 5 AM  
- **Security updates**: Immediate (any time)

## Review Process

1. Renovate creates PR with dependency updates
2. Automated validation runs via GitHub Actions
3. PR comment shows validation results:
   - ✅ Safe to merge (all validations passed)
   - ❌ Requires review (validation failed)
4. Platform team reviews and merges

## Supported Ecosystems

- **Node.js**: npm/pnpm packages with ESLint protection
- **Python**: pip packages via requirements.txt and pyproject.toml
- **Docker**: Base image updates with security focus

## Emergency Override

If urgent updates are needed that fail validation:

1. Create manual PR with necessary changes
2. Include justification in PR description
3. Get platform team approval
4. Update validation rules if needed
