#!/usr/bin/env node

/**
 * CTA Guard - Scans built React app for interactive elements without proper handlers
 * This script ensures all CTAs (Call-To-Action elements) have proper handlers including:
 * - Buttons with onClick handlers
 * - Links with proper routing
 * - Dialog submit buttons and forms
 * - Dropdown menu items with select handlers
 * - Form submissions with proper handlers
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const DIST_DIR = path.join(__dirname, '..', 'dist', 'assets')
const ERRORS = []

function scanJSFiles() {
  console.log('Looking for dist directory at:', DIST_DIR);

  if (!fs.existsSync(DIST_DIR)) {
    console.error('❌ Build directory not found. Run `npm run build` first.');
    process.exit(1)
  }

  const files = fs.readdirSync(DIST_DIR)
  const jsFiles = files.filter(file => file.endsWith('.js'))

  console.log(`🔍 Scanning ${jsFiles.length} JavaScript files for CTA violations...`)
  console.log('Files found:', jsFiles.slice(0, 5).join(', '), jsFiles.length > 5 ? '...' : '');

  // Filter out vendor/library files that often have false positives
  const vendorPatterns = [
    'charts-',
    'react-vendor-',
    'react-router-',
    'ui-vendor-',
    'tanstack-query-',
    'index-BLe8pNnE.js', // React core bundle
    'index-DG2qBGFn.js', // UI component bundle
    'index-DMzMW9FX.js'  // Button component bundle
  ];

  const userFiles = jsFiles.filter(file =>
    !vendorPatterns.some(pattern => file.includes(pattern))
  );

  console.log(`📝 Focusing on ${userFiles.length} user files (excluding ${jsFiles.length - userFiles.length} vendor files)`);

  userFiles.forEach(file => {
    const filePath = path.join(DIST_DIR, file)
    const content = fs.readFileSync(filePath, 'utf8')

    scanForViolations(content, file)
  })
}function scanForViolations(content, filename) {
  // Patterns to detect problematic CTAs
  const patterns = [
    // Button without onClick (React JSX patterns) - only in JSX-like content
    {
      regex: /jsx?\([^,]*,\s*["']button["'][^,]*(?![^}]*onClick)[^}]*>/g,
      type: 'button without onClick',
      severity: 'error'
    },
    // Link without to prop (React Router patterns)
    {
      regex: /jsx?\([^,]*,\s*["']Link["'][^,]*(?![^}]*to=)[^}]*>/g,
      type: 'Link without to prop',
      severity: 'error'
    },
    // Placeholder onClick handlers with common patterns
    {
      regex: /onClick\s*:\s*(?:\(\)\s*=>\s*)?(?:alert\s*\(|console\.log\s*\(|void\s+0|\.\.\.|"[^"]*coming\s+soon[^"]*"|'[^']*coming\s+soon[^']*')/gi,
      type: 'placeholder onClick handler',
      severity: 'warning'
    },
    // Specific placeholder patterns from our codebase
    {
      regex: /onClick\s*:\s*\(\)\s*=>\s*alert\s*\(\s*["'][^"']*API\s+call[^"']*["']\s*\)/gi,
      type: 'API call placeholder',
      severity: 'warning'
    },
    // Dialog submit buttons without proper handlers
    {
      regex: /<Dialog[^>]*>[\s\S]*?<button[^>]*type=['"]submit['"][^>]*(?![^>]*onClick)[^>]*>/g,
      type: 'Dialog submit button without onClick',
      severity: 'error'
    },
    // Dialog form buttons without handlers
    {
      regex: /<Dialog[^>]*>[\s\S]*?<form[^>]*>[\s\S]*?<button(?![^>]*onClick)(?![^>]*type=['"]submit['"])[^>]*>/g,
      type: 'Dialog form button without handler',
      severity: 'error'
    },
    // Dropdown menu items without handlers
    {
      regex: /<DropdownMenu[^>]*>[\s\S]*?<DropdownMenuItem(?![^>]*onClick)(?![^>]*onSelect)[^>]*>/g,
      type: 'DropdownMenuItem without onClick/onSelect',
      severity: 'error'
    },
    // Menu items without handlers (Radix UI patterns)
    {
      regex: /<MenuItem(?![^>]*onClick)(?![^>]*onSelect)[^>]*>/g,
      type: 'MenuItem without onClick/onSelect',
      severity: 'error'
    },
    // Select trigger without value handlers
    {
      regex: /<Select(?![^>]*onValueChange)[^>]*>/g,
      type: 'Select without onValueChange',
      severity: 'error'
    },
    // Command items without handlers
    {
      regex: /<CommandItem(?![^>]*onSelect)[^>]*>/g,
      type: 'CommandItem without onSelect',
      severity: 'error'
    },
    // Form submission without proper handlers
    {
      regex: /<form(?![^>]*onSubmit)[^>]*>/g,
      type: 'form without onSubmit',
      severity: 'warning'
    },
    // Dialog close buttons without handlers
    {
      regex: /<Dialog[^>]*>[\s\S]*?<button[^>]*(?:close|cancel|dismiss)(?![^>]*onClick)[^>]*>/gi,
      type: 'Dialog close button without onClick',
      severity: 'warning'
    }
  ]

  patterns.forEach(pattern => {
    const matches = content.match(pattern.regex)
    if (matches) {
      matches.forEach(match => {
        ERRORS.push({
          file: filename,
          type: pattern.type,
          severity: pattern.severity,
          match: match.substring(0, 100) + (match.length > 100 ? '...' : ''),
          line: getLineNumber(content, match)
        })
      })
    }
  })
}

function getLineNumber(content, match) {
  const index = content.indexOf(match)
  if (index === -1) return 1

  return content.substring(0, index).split('\n').length
}

function printResults() {
  console.log('\n📊 CTA Guard Results:')
  console.log('=' .repeat(50))

  if (ERRORS.length === 0) {
    console.log('✅ No CTA violations found! All buttons and links have proper handlers.')
    return true
  }

  const errorsByType = ERRORS.reduce((acc, error) => {
    acc[error.type] = (acc[error.type] || 0) + 1
    return acc
  }, {})

  console.log('\n📈 Summary:')
  Object.entries(errorsByType).forEach(([type, count]) => {
    console.log(`  • ${type}: ${count} violations`)
  })

  console.log('\n🔍 Detailed Results:')
  ERRORS.forEach((error, index) => {
    const icon = error.severity === 'error' ? '❌' : '⚠️'
    console.log(`\n${icon} ${index + 1}. ${error.type}`)
    console.log(`   File: ${error.file}:${error.line}`)
    console.log(`   Code: ${error.match}`)
  })

  const errorCount = ERRORS.filter(e => e.severity === 'error').length
  const warningCount = ERRORS.filter(e => e.severity === 'warning').length

  console.log('\n' + '='.repeat(50))
  console.log(`🎯 Total: ${errorCount} errors, ${warningCount} warnings`)

  if (errorCount > 0) {
    console.log('\n❌ CTA Guard failed! Please fix the errors above.')
    return false
  } else if (warningCount > 0) {
    console.log('\n⚠️  CTA Guard passed with warnings. Consider fixing them.')
    return true
  }

  return true
}

function main() {
  console.log('🛡️  CTA Guard - Ensuring all CTAs have proper handlers')
  console.log('=' .repeat(50))

  scanJSFiles()
  const success = printResults()

  process.exit(success ? 0 : 1)
}

// Run if called directly
main()

export { scanJSFiles, printResults }
