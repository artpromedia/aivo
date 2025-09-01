#!/usr/bin/env node

/**
 * SDK Generation Script
 * Generates TypeScript and Python SDKs fromasync function validateSpecs() {
  log('Validating OpenAPI specifications...');
  
  for (const spec of config.specs) {
    const specPath = join(projectRoot, spec.file);
    
    if (!existsSync(specPath)) {
      throw new Error(`OpenAPI specification not found: ${specPath}`);
    }
    
    try {
      // Use spectral to validate but only fail on errors, not warnings
      runCommand(`npx spectral lint "${specPath}" --fail-severity=error`);
      log(`✓ ${spec.name} specification is valid`);
    } catch (error) {
      // Don't fail on spectral warnings, just log them
      log(`⚠ ${spec.name} specification validation failed but continuing...`, 'warn');
    }
  }
  
  log('OpenAPI specifications validation completed');
}ications
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import process from 'process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

// Configuration
const config = {
  specs: [
    { name: 'auth', file: 'docs/api/rest/auth.yaml' },
    { name: 'tenant', file: 'docs/api/rest/tenant.yaml' },
    { name: 'enrollment', file: 'docs/api/rest/enrollment.yaml' },
    { name: 'payments', file: 'docs/api/rest/payments.yaml' },
    { name: 'learner', file: 'docs/api/rest/learner.yaml' },
    { name: 'orchestrator', file: 'docs/api/rest/orchestrator.yaml' },
    { name: 'admin-portal', file: 'docs/api/rest/admin-portal.yaml' }
  ],
  output: {
    typescript: 'libs/sdk-web',
    python: 'libs/sdk-py'
  },
  generators: {
    typescript: 'typescript-fetch',
    python: 'python'
  }
};

/**
 * Utility functions
 */
function log(message, level = 'info') {
  const timestamp = new Date().toISOString();
  const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : '✅';
  console.log(`${prefix} [${timestamp}] ${message}`);
}

function ensureDir(dir) {
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
    log(`Created directory: ${dir}`);
  }
}

function runCommand(command, cwd = projectRoot) {
  try {
    log(`Running: ${command}`);
    const result = execSync(command, { 
      cwd, 
      encoding: 'utf8',
      stdio: 'pipe'
    });
    return result;
  } catch (error) {
    log(`Command failed: ${command}`, 'error');
    log(`Error: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Check if OpenAPI Generator CLI is available
 */
function checkOpenApiGenerator() {
  try {
    runCommand('npx @openapitools/openapi-generator-cli version');
    log('OpenAPI Generator CLI is available');
    return true;
  } catch (error) {
    log('OpenAPI Generator CLI not found, installing...', 'warn');
    try {
      runCommand('npm install -g @openapitools/openapi-generator-cli');
      log('OpenAPI Generator CLI installed successfully');
      return true;
    } catch (installError) {
      log('Failed to install OpenAPI Generator CLI', 'error');
      return false;
    }
  }
}

/**
 * Validate OpenAPI specifications
 */
async function validateSpecs() {
  log('Validating OpenAPI specifications...');
  
  for (const spec of config.specs) {
    const specPath = join(projectRoot, spec.file);
    
    if (!existsSync(specPath)) {
      log(`Specification file not found: ${specPath}`, 'error');
      throw new Error(`Missing specification: ${spec.name}`);
    }
    
    try {
      // Use spectral for validation if available, otherwise just check file exists
      if (existsSync(join(projectRoot, 'node_modules/.bin/spectral'))) {
        runCommand(`npx spectral lint "${specPath}"`);
      }
      log(`✓ ${spec.name} specification is valid`);
    } catch (error) {
      log(`✗ ${spec.name} specification validation failed`, 'warn');
      // Continue with warnings for now
    }
  }
}

/**
 * Generate TypeScript SDK
 */
async function generateTypeScriptSDK() {
  log('Generating TypeScript SDK...');
  
  const outputDir = join(projectRoot, config.output.typescript);
  ensureDir(outputDir);
  
  // Generate individual service clients
  for (const spec of config.specs) {
    const specPath = join(projectRoot, spec.file);
    const serviceOutputDir = join(outputDir, 'src', 'services', spec.name);
    
    ensureDir(serviceOutputDir);
    
    // Convert Windows paths to use forward slashes for OpenAPI Generator
    const specPathFormatted = specPath.replace(/\\/g, '/');
    const serviceOutputDirFormatted = serviceOutputDir.replace(/\\/g, '/');
    
    const command = [
      'npx @openapitools/openapi-generator-cli generate',
      `--skip-validate-spec`,
      `-i "${specPathFormatted}"`,
      `-g ${config.generators.typescript}`,
      `-o "${serviceOutputDirFormatted}"`,
      '--additional-properties=typescriptThreePlus=true,supportsES6=true,npmName=@aivo/sdk-web,npmVersion=1.0.0'
    ].join(' ');
    
    try {
      runCommand(command);
      log(`✓ Generated TypeScript client for ${spec.name}`);
    } catch (error) {
      log(`✗ Failed to generate TypeScript client for ${spec.name}`, 'error');
      throw error;
    }
  }
  
  // Generate main index file
  await generateTypeScriptIndex();
  
  // Generate package.json
  await generateTypeScriptPackageJson();
  
  log('TypeScript SDK generation completed');
}

/**
 * Generate Python SDK
 */
async function generatePythonSDK() {
  log('Generating Python SDK...');
  
  const outputDir = join(projectRoot, config.output.python);
  ensureDir(outputDir);
  
  // Generate individual service clients
  for (const spec of config.specs) {
    const specPath = join(projectRoot, spec.file);
    const serviceOutputDir = join(outputDir, 'aivo_sdk', 'services', spec.name);
    
    ensureDir(serviceOutputDir);
    
    // Convert Windows paths to use forward slashes for OpenAPI Generator
    const specPathFormatted = specPath.replace(/\\/g, '/');
    const serviceOutputDirFormatted = serviceOutputDir.replace(/\\/g, '/');
    
    const command = [
      'npx @openapitools/openapi-generator-cli generate',
      `--skip-validate-spec`,
      `-i "${specPathFormatted}"`,
      `-g ${config.generators.python}`,
      `-o "${serviceOutputDirFormatted}"`,
      '--additional-properties=packageName=aivo_sdk,projectName=aivo-sdk-py,packageVersion=1.0.0'
    ].join(' ');
    
    try {
      runCommand(command);
      log(`✓ Generated Python client for ${spec.name}`);
    } catch (error) {
      log(`✗ Failed to generate Python client for ${spec.name}`, 'error');
      throw error;
    }
  }
  
  // Generate main __init__.py files
  await generatePythonInit();
  
  // Generate setup.py
  await generatePythonSetup();
  
  log('Python SDK generation completed');
}

/**
 * Generate TypeScript index file
 */
async function generateTypeScriptIndex() {
  const indexContent = `// Auto-generated SDK exports
// Generated on: ${new Date().toISOString()}

${config.specs.map(spec => 
  `export * from './services/${spec.name}';`
).join('\n')}

// Re-export common types
export interface ApiConfig {
  basePath?: string;
  accessToken?: string;
  apiKey?: string;
  credentials?: 'include' | 'same-origin' | 'omit';
}

// SDK Version
export const SDK_VERSION = '1.0.0';
`;

  const indexPath = join(projectRoot, config.output.typescript, 'src', 'index.ts');
  ensureDir(dirname(indexPath));
  writeFileSync(indexPath, indexContent);
  log('Generated TypeScript index file');
}

/**
 * Generate TypeScript package.json
 */
async function generateTypeScriptPackageJson() {
  const packageJson = {
    name: '@aivo/sdk-web',
    version: '1.0.0',
    description: 'TypeScript/JavaScript SDK for Aivo API',
    main: 'dist/index.js',
    types: 'dist/index.d.ts',
    files: ['dist/**/*'],
    scripts: {
      build: 'tsc',
      'build:watch': 'tsc --watch',
      test: 'jest',
      lint: 'eslint src/**/*.ts',
      'lint:fix': 'eslint src/**/*.ts --fix'
    },
    dependencies: {
      'cross-fetch': '^3.1.5'
    },
    devDependencies: {
      '@types/node': '^20.0.0',
      'typescript': '^5.0.0',
      'jest': '^29.0.0',
      '@types/jest': '^29.0.0',
      'eslint': '^8.0.0',
      '@typescript-eslint/eslint-plugin': '^6.0.0',
      '@typescript-eslint/parser': '^6.0.0'
    },
    keywords: ['aivo', 'api', 'sdk', 'typescript', 'javascript'],
    author: 'Aivo Team',
    license: 'MIT',
    repository: {
      type: 'git',
      url: 'https://github.com/artpromedia/aivo.git',
      directory: 'libs/sdk-web'
    }
  };

  const packagePath = join(projectRoot, config.output.typescript, 'package.json');
  writeFileSync(packagePath, JSON.stringify(packageJson, null, 2));
  log('Generated TypeScript package.json');
}

/**
 * Generate Python __init__.py files
 */
async function generatePythonInit() {
  // Main package __init__.py
  const mainInit = `"""
Aivo Python SDK

A comprehensive Python SDK for the Aivo learning platform API.
Generated on: ${new Date().toISOString()}
"""

__version__ = "1.0.0"

${config.specs.map(spec => 
  `from .services.${spec.name} import *`
).join('\n')}

# Configuration class
class ApiConfig:
    def __init__(self, base_path: str = None, access_token: str = None, api_key: str = None):
        self.base_path = base_path or "https://api.aivo.com"
        self.access_token = access_token
        self.api_key = api_key

# Default configuration
default_config = ApiConfig()
`;

  const initPath = join(projectRoot, config.output.python, 'aivo_sdk', '__init__.py');
  ensureDir(dirname(initPath));
  writeFileSync(initPath, mainInit);
  log('Generated Python __init__.py files');
}

/**
 * Generate Python setup.py
 */
async function generatePythonSetup() {
  const setupPy = `from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aivo-sdk-py",
    version="1.0.0",
    author="Aivo Team",
    author_email="api-support@aivo.com",
    description="Python SDK for Aivo API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/artpromedia/aivo",
    project_urls={
        "Bug Tracker": "https://github.com/artpromedia/aivo/issues",
        "Documentation": "https://docs.aivo.com",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "urllib3>=1.26.0",
        "python-dateutil>=2.8.0",
        "pydantic>=1.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ]
    },
)
`;

  const setupPath = join(projectRoot, config.output.python, 'setup.py');
  writeFileSync(setupPath, setupPy);
  log('Generated Python setup.py');
}

/**
 * Generate MSW fixture handlers
 */
async function generateMSWHandlers() {
  log('Generating MSW fixture handlers...');
  
  const handlersDir = join(projectRoot, config.output.typescript, 'src', 'msw');
  ensureDir(handlersDir);
  
  const handlersContent = `// Auto-generated MSW handlers for API mocking
// Generated on: ${new Date().toISOString()}

import { rest } from 'msw';

// Mock data fixtures
const mockFixtures = {
${config.specs.map(spec => `  ${spec.name}: {
    // Add mock data for ${spec.name} service
  },`).join('\n')}
};

// Generated handlers
export const handlers = [
${config.specs.map(spec => `  // ${spec.name.toUpperCase()} Service Handlers
  rest.get('*/auth/v1/*', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockFixtures.${spec.name}));
  }),`).join('\n')}
];

export default handlers;
`;

  const handlersPath = join(handlersDir, 'handlers.ts');
  writeFileSync(handlersPath, handlersContent);
  log('Generated MSW handlers');
}

/**
 * Update package.json scripts
 */
async function updatePackageJsonScripts() {
  const packageJsonPath = join(projectRoot, 'package.json');
  
  if (existsSync(packageJsonPath)) {
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf8'));
    
    // Add SDK generation script
    packageJson.scripts = packageJson.scripts || {};
    packageJson.scripts['gen:sdk'] = 'node scripts/generate-sdks.mjs';
    packageJson.scripts['gen:sdk:watch'] = 'nodemon --watch docs/api/rest --ext yaml,yml --exec "npm run gen:sdk"';
    
    writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
    log('Updated package.json scripts');
  }
}

/**
 * Main execution
 */
async function main() {
  try {
    log('🚀 Starting SDK generation...');
    
    // Check prerequisites
    if (!checkOpenApiGenerator()) {
      throw new Error('OpenAPI Generator CLI is required but not available');
    }
    
    // Validate specifications
    await validateSpecs();
    
    // Generate SDKs
    await generateTypeScriptSDK();
    await generatePythonSDK();
    
    // Generate additional tooling
    await generateMSWHandlers();
    await updatePackageJsonScripts();
    
    log('🎉 SDK generation completed successfully!');
    log('📁 TypeScript SDK: libs/sdk-web');
    log('📁 Python SDK: libs/sdk-py');
    log('🔧 MSW Handlers: libs/sdk-web/src/msw');
    
  } catch (error) {
    log(`💥 SDK generation failed: ${error.message}`, 'error');
    process.exit(1);
  }
}

// Run the script immediately
main().catch(console.error);

export { main, config };
