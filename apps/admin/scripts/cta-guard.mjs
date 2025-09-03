#!/usr/bin/env node

/**
 * CTA Guard - Scans built React app for buttons without onClick handlers
 * This script ensures all CTAs (Call-To-Action elements) have proper handlers
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const DIST_DIR = path.join(__dirname, '..', 'dist', 'assets')
const ERRORS = []

function scanJSFiles() {
  if (!fs.existsSync(DIST_DIR)) {
    console.error('❌ Build directory not found. Run `npm run build` first.')
    process.exit(1)
  }

  const files = fs.readdirSync(DIST_DIR)
  const jsFiles = files.filter(file => file.endsWith('.js'))

  console.log(`🔍 Scanning ${jsFiles.length} JavaScript files for CTA violations...`)

  jsFiles.forEach(file => {
    const filePath = path.join(DIST_DIR, file)
    const content = fs.readFileSync(filePath, 'utf8')
    
    scanForViolations(content, file)
  })
}

function scanForViolations(content, filename) {
  // Patterns to detect problematic CTAs
  const patterns = [
    // Button without onClick (React JSX patterns)
    {
      regex: /<button(?![^>]*onClick)[^>]*>/g,
      type: 'button without onClick',
      severity: 'error'
    },
    // Link without to prop (React Router patterns)
    {
      regex: /<Link(?![^>]*to=)[^>]*>/g,
      type: 'Link without to prop',
      severity: 'error'
    },
    // Anchor without href
    {
      regex: /<a(?![^>]*href)[^>]*>/g,
      type: 'anchor without href',
      severity: 'error'
    },
    // Button with placeholder text (static CTA indicators)
    {
      regex: /onClick.*(?:alert\s*\(\s*['"]\s*|console\.log\s*\(\s*['"]\s*|\.\.\.)/g,
      type: 'placeholder onClick handler',
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
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
}

export { scanJSFiles, printResults }
