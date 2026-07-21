#!/usr/bin/env node
/**
 * i18n Audit Script
 * Finds hardcoded Chinese text outside of locale files
 * Run: node scripts/auditI18n.js
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')

const SCAN_DIRS = ['src']
const EXTENSIONS = ['.vue', '.js', '.ts']
const EXCLUDE = ['node_modules', 'dist', 'locales', 'i18n', '.spec.', '.test.']

const CHINESE_REGEX = /[\u4e00-\u9fa5\u3400-\u4dbf]/g
const ALLOWED_PATTERNS = [/^\s*\/\//, /^\s*\*/, /console\.(log|warn|error|info)/]

function isAllowedLine(line) {
  return ALLOWED_PATTERNS.some(p => p.test(line))
}

function walkDir(dir, files = []) {
  if (!fs.existsSync(dir)) return files
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (EXCLUDE.some(ex => fullPath.includes(ex))) continue
    if (entry.isDirectory()) {
      walkDir(fullPath, files)
    } else if (EXTENSIONS.some(ext => entry.name.endsWith(ext))) {
      files.push(fullPath)
    }
  }
  return files
}

function findChineseInFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8')
  const lines = content.split('\n')
  const violations = []
  lines.forEach((line, index) => {
    if (CHINESE_REGEX.test(line) && !isAllowedLine(line)) {
      const matches = line.match(CHINESE_REGEX)
      violations.push({
        line: index + 1,
        content: line.trim().substring(0, 80),
        chars: matches ? matches.join('') : ''
      })
    }
  })
  return violations
}

function auditI18n() {
  console.log('Auditing for hardcoded Chinese text...\n')
  const fileViolations = []
  let totalFiles = 0

  for (const scanDir of SCAN_DIRS) {
    const absDir = path.join(ROOT, scanDir)
    const files = walkDir(absDir)
    for (const file of files) {
      totalFiles++
      const violations = findChineseInFile(file)
      if (violations.length > 0) {
        fileViolations.push({ file: path.relative(ROOT, file), violations })
      }
    }
  }

  console.log(`Checked ${totalFiles} source files\n`)

  if (fileViolations.length > 0) {
    console.error('FAILED: Hardcoded Chinese text found!\n')
    let totalViolations = 0
    fileViolations.forEach(({ file, violations }) => {
      console.error(`  ${file}`)
      violations.forEach(v => {
        totalViolations++
        console.error(`    Line ${v.line}: ${v.content}`)
      })
      console.error('')
    })
    console.error(`Total files: ${fileViolations.length}, Violations: ${totalViolations}`)
    console.error('\nPlease move Chinese text to i18n locale files.')
    process.exit(1)
  }

  console.log('PASSED: No hardcoded Chinese text found')
  process.exit(0)
}

auditI18n()
