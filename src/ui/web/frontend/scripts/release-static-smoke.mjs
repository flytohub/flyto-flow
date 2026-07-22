import fs from 'node:fs'
import path from 'node:path'

const root = process.cwd()
const distDir = path.join(root, 'dist')
const htmlPath = path.join(distDir, 'index.html')
const outDir = path.resolve(root, '../../../..', 'out', 'release')
const reportPath = path.join(outDir, 'cloud-frontend-static-smoke.json')

function fail(message) {
  throw new Error(message)
}

if (!fs.existsSync(htmlPath)) {
  fail('dist/index.html is missing. Run npm run build before release:static-smoke.')
}

const html = fs.readFileSync(htmlPath, 'utf8')
const assetRefs = [...html.matchAll(/(?:src|href)="([^"]+)"/g)]
  .map((match) => match[1])
  .filter((ref) => ref.startsWith('/assets/') || ref.startsWith('assets/'))

const missingAssets = []
for (const ref of assetRefs) {
  const normalized = ref.replace(/^\//, '')
  const assetPath = path.join(distDir, normalized)
  if (!fs.existsSync(assetPath)) {
    missingAssets.push(ref)
  }
}

const jsFiles = []
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const entryPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      walk(entryPath)
    } else if (entry.name.endsWith('.js')) {
      jsFiles.push(entryPath)
    }
  }
}
walk(distDir)

const publicSourceMapRefs = []
for (const filePath of jsFiles) {
  const text = fs.readFileSync(filePath, 'utf8')
  if (/sourceMappingURL=/.test(text)) {
    publicSourceMapRefs.push(path.relative(root, filePath))
  }
}

const violations = []
if (assetRefs.length === 0) {
  violations.push('index.html does not reference any built assets')
}
if (missingAssets.length > 0) {
  violations.push(`missing built assets: ${missingAssets.join(', ')}`)
}
if (publicSourceMapRefs.length > 0) {
  violations.push(`public sourceMappingURL references found: ${publicSourceMapRefs.join(', ')}`)
}

const report = {
  project: 'flyto2-flow',
  surface: 'web-frontend',
  generatedAt: new Date().toISOString(),
  html: path.relative(root, htmlPath),
  assetRefCount: assetRefs.length,
  jsFileCount: jsFiles.length,
  missingAssets,
  publicSourceMapRefs,
  violations,
}

fs.mkdirSync(outDir, { recursive: true })
fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`)

if (violations.length > 0) {
  console.error(`Release static smoke failed. Report: ${reportPath}`)
  for (const violation of violations) {
    console.error(`- ${violation}`)
  }
  process.exit(1)
}

console.log(`Release static smoke passed: ${assetRefs.length} html assets, ${jsFiles.length} JS files`)
