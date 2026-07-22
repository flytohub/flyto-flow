import fs from 'node:fs'
import path from 'node:path'
import zlib from 'node:zlib'

const root = process.cwd()
const assetsDir = path.join(root, 'dist', 'assets')
const indexHtmlPath = path.join(root, 'dist', 'index.html')
const outDir = path.resolve(root, '../../../..', 'out', 'release')
const reportPath = path.join(outDir, 'cloud-frontend-bundle-budget.json')

const budget = {
  totalGzipBytes: 7_430_000,
  largestChunkGzipBytes: 3_320_000,
  secondLargestChunkGzipBytes: 820_000,
  monacoEditorGzipBytes: 720_000,
  policy: 'Cloud frontend still has anonymous legacy chunks; block growth beyond current baseline plus 10%; Monaco editor may be large but must stay lazy-loaded.',
}

function fail(message) {
  throw new Error(message)
}

if (!fs.existsSync(assetsDir)) {
  fail('dist/assets is missing. Run npm run build before release:bundle-budget.')
}
if (!fs.existsSync(indexHtmlPath)) {
  fail('dist/index.html is missing. Run npm run build before release:bundle-budget.')
}

const chunks = fs.readdirSync(assetsDir)
  .filter((name) => name.endsWith('.js'))
  .map((name) => {
    const filePath = path.join(assetsDir, name)
    const bytes = fs.readFileSync(filePath)
    return {
      name,
      rawBytes: bytes.byteLength,
      gzipBytes: zlib.gzipSync(bytes).byteLength,
    }
  })
  .sort((a, b) => b.gzipBytes - a.gzipBytes)

if (chunks.length === 0) {
  fail('No JavaScript chunks found in dist/assets.')
}

const totalGzipBytes = chunks.reduce((total, chunk) => total + chunk.gzipBytes, 0)
const indexHtml = fs.readFileSync(indexHtmlPath, 'utf8')
const modulePreloads = [...indexHtml.matchAll(/<link\s+rel="modulepreload"[^>]+href="\/assets\/([^"]+\.js)"/g)]
  .map((match) => match[1])
const monacoChunks = chunks.filter((chunk) => chunk.name.startsWith('vendor-monaco-'))
const violations = []

if (totalGzipBytes > budget.totalGzipBytes) {
  violations.push(`total gzip ${totalGzipBytes} exceeds budget ${budget.totalGzipBytes}`)
}
if (chunks[0]?.gzipBytes > budget.largestChunkGzipBytes) {
  violations.push(`${chunks[0].name} gzip ${chunks[0].gzipBytes} exceeds largest chunk budget ${budget.largestChunkGzipBytes}`)
}
if (chunks[1]?.gzipBytes > budget.secondLargestChunkGzipBytes) {
  violations.push(`${chunks[1].name} gzip ${chunks[1].gzipBytes} exceeds second largest chunk budget ${budget.secondLargestChunkGzipBytes}`)
}
for (const chunk of monacoChunks) {
  if (chunk.gzipBytes > budget.monacoEditorGzipBytes) {
    violations.push(`${chunk.name} gzip ${chunk.gzipBytes} exceeds lazy Monaco budget ${budget.monacoEditorGzipBytes}`)
  }
  if (modulePreloads.includes(chunk.name)) {
    violations.push(`${chunk.name} is modulepreloaded by dist/index.html but must remain lazy-loaded`)
  }
}

const report = {
  project: 'flyto2-flow',
  surface: 'web-frontend',
  generatedAt: new Date().toISOString(),
  budget,
  totalGzipBytes,
  chunkCount: chunks.length,
  modulePreloads,
  monacoChunks,
  topChunks: chunks.slice(0, 20),
  violations,
}

fs.mkdirSync(outDir, { recursive: true })
fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`)

if (violations.length > 0) {
  console.error(`Release bundle budget failed. Report: ${reportPath}`)
  for (const violation of violations) {
    console.error(`- ${violation}`)
  }
  process.exit(1)
}

console.log(`Release bundle budget passed: ${chunks.length} chunks, ${Math.round(totalGzipBytes / 1024)} KiB gzip`)
