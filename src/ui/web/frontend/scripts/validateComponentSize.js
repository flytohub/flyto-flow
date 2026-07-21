#!/usr/bin/env node
/**
 * Component Size Validator
 * Fails build if any component exceeds MAX_LINES
 * Run: node scripts/validateComponentSize.js
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')

const MAX_LINES = 900    // Hard fail — nothing should exceed this
const WARN_LINES = 500   // Warning — should be split when possible
const SCAN_DIRS = ['src/components', 'src/views']
const EXCLUDE = ['node_modules', 'dist', '.spec.vue', '.test.vue']

function countLines(filePath) {
  return fs.readFileSync(filePath, 'utf-8').split('\n').length
}

function walkDir(dir, files = []) {
  if (!fs.existsSync(dir)) return files
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (EXCLUDE.some(ex => fullPath.includes(ex))) continue
    if (entry.isDirectory()) {
      walkDir(fullPath, files)
    } else if (entry.name.endsWith('.vue')) {
      files.push(fullPath)
    }
  }
  return files
}

function validateComponentSizes() {
  console.log('Validating component sizes...')
  console.log(`Max allowed lines: ${MAX_LINES}\n`)

  const violations = []
  let totalFiles = 0

  for (const scanDir of SCAN_DIRS) {
    const absDir = path.join(ROOT, scanDir)
    const files = walkDir(absDir)
    for (const file of files) {
      totalFiles++
      const lines = countLines(file)
      if (lines > MAX_LINES) {
        violations.push({
          file: path.relative(ROOT, file),
          lines,
          excess: lines - MAX_LINES
        })
      }
    }
  }

  console.log(`Checked ${totalFiles} component files\n`)

  // Warnings (300-500 lines)
  const warnings = []
  for (const scanDir of SCAN_DIRS) {
    const absDir = path.join(ROOT, scanDir)
    const files = walkDir(absDir)
    for (const file of files) {
      const lines = countLines(file)
      if (lines > WARN_LINES && lines <= MAX_LINES) {
        warnings.push({ file: path.relative(ROOT, file), lines })
      }
    }
  }

  if (warnings.length > 0) {
    console.warn(`WARNING: ${warnings.length} components exceed ${WARN_LINES} lines (consider splitting):\n`)
    warnings.sort((a, b) => b.lines - a.lines).slice(0, 10).forEach(w => {
      console.warn(`  ${w.file} (${w.lines} lines)`)
    })
    console.warn('')
  }

  if (violations.length > 0) {
    console.error('FAILED: Component size violations found!\n')
    console.error(`Files exceeding ${MAX_LINES} line limit:\n`)
    violations.sort((a, b) => b.lines - a.lines).forEach(v => {
      console.error(`  ${v.file}`)
      console.error(`    Lines: ${v.lines} (+${v.excess})\n`)
    })
    console.error(`Total violations: ${violations.length}`)
    console.error('\nPlease split these components into smaller files.')
    process.exit(1)
  }

  console.log('PASSED: All components within size limits')
  process.exit(0)
}

validateComponentSizes()
