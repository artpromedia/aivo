#!/usr/bin/env node
/**
 * Renovate Update Validator
 * Ensures that Renovate updates don't violate our dependency policies
 */

import fs from 'node:fs';
import { execSync } from 'node:child_process';

const ESLINT_MIN_VERSION = '9.0.0';
const TYPESCRIPT_ESLINT_MIN_VERSION = '8.0.0';

function log(level, message) {
  const timestamp = new Date().toISOString();
  const colors = {
    info: '\x1b[36m',
    success: '\x1b[32m',
    warning: '\x1b[33m',
    error: '\x1b[31m',
    reset: '\x1b[0m'
  };
  console.log(`${colors[level]}[${timestamp}] ${level.toUpperCase()}: ${message}${colors.reset}`);
}

function compareVersions(version1, version2) {
  const parts1 = version1.split('.').map(Number);
  const parts2 = version2.split('.').map(Number);
  
  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const part1 = parts1[i] || 0;
    const part2 = parts2[i] || 0;
    
    if (part1 > part2) return 1;
    if (part1 < part2) return -1;
  }
  return 0;
}

function getPackageVersion(packageName) {
  try {
    const result = execSync(`npm list ${packageName} --depth=0 --json`, { 
      stdio: ['ignore', 'pipe', 'ignore'] 
    }).toString();
    const data = JSON.parse(result);
    return data.dependencies?.[packageName]?.version;
  } catch {
    return null;
  }
}

function validateESLintVersion() {
  log('info', 'Validating ESLint version...');
  
  const eslintVersion = getPackageVersion('eslint');
  if (!eslintVersion) {
    log('error', 'ESLint not found in dependencies');
    return false;
  }
  
  const cleanVersion = eslintVersion.replace(/[^0-9.]/g, '');
  if (compareVersions(cleanVersion, ESLINT_MIN_VERSION) < 0) {
    log('error', `ESLint version ${eslintVersion} is below minimum required version ${ESLINT_MIN_VERSION}`);
    return false;
  }
  
  log('success', `ESLint version ${eslintVersion} meets requirements`);
  return true;
}

function validateTypeScriptESLint() {
  log('info', 'Validating TypeScript ESLint compatibility...');
  
  const tsEslintVersion = getPackageVersion('@typescript-eslint/eslint-plugin');
  if (!tsEslintVersion) {
    log('info', 'TypeScript ESLint plugin not found (optional)');
    return true;
  }
  
  const cleanVersion = tsEslintVersion.replace(/[^0-9.]/g, '');
  if (compareVersions(cleanVersion, TYPESCRIPT_ESLINT_MIN_VERSION) < 0) {
    log('error', `TypeScript ESLint version ${tsEslintVersion} may not be compatible with ESLint v9`);
    return false;
  }
  
  log('success', `TypeScript ESLint version ${tsEslintVersion} is compatible`);
  return true;
}

function validateNoDeprecatedPackages() {
  log('info', 'Checking for deprecated packages...');
  
  try {
    execSync('node scripts/check-npm-deprecations.mjs', { stdio: 'pipe' });
    log('success', 'No deprecated packages found');
    return true;
  } catch (error) {
    log('error', 'Deprecated packages detected');
    return false;
  }
}

function validatePackageIntegrity() {
  log('info', 'Validating package integrity...');
  
  try {
    // Check if pnpm install works
    execSync('pnpm install --frozen-lockfile', { stdio: 'pipe' });
    log('success', 'Package integrity validated');
    return true;
  } catch (error) {
    log('error', 'Package integrity check failed');
    return false;
  }
}

function validateLinting() {
  log('info', 'Running lint validation...');
  
  try {
    execSync('pnpm run lint', { stdio: 'pipe' });
    log('success', 'Lint validation passed');
    return true;
  } catch (error) {
    log('error', 'Lint validation failed');
    return false;
  }
}

async function main() {
  log('info', '🤖 Starting Renovate update validation...');
  
  const validations = [
    { name: 'ESLint Version', fn: validateESLintVersion },
    { name: 'TypeScript ESLint Compatibility', fn: validateTypeScriptESLint },
    { name: 'No Deprecated Packages', fn: validateNoDeprecatedPackages },
    { name: 'Package Integrity', fn: validatePackageIntegrity },
    { name: 'Lint Validation', fn: validateLinting }
  ];
  
  let allPassed = true;
  const results = [];
  
  for (const validation of validations) {
    log('info', `Running ${validation.name}...`);
    const passed = validation.fn();
    results.push({ name: validation.name, passed });
    
    if (!passed) {
      allPassed = false;
    }
  }
  
  log('info', '📊 Validation Summary:');
  results.forEach(result => {
    const status = result.passed ? '✅ PASS' : '❌ FAIL';
    log(result.passed ? 'success' : 'error', `${result.name}: ${status}`);
  });
  
  if (allPassed) {
    log('success', '🎉 All validations passed! Renovate update is safe to merge.');
    process.exit(0);
  } else {
    log('error', '💥 Some validations failed! Review the Renovate update before merging.');
    process.exit(1);
  }
}

main().catch(error => {
  log('error', `Validation failed with error: ${error.message}`);
  process.exit(1);
});
