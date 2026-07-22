import fs from 'node:fs'
import http from 'node:http'
import path from 'node:path'
import { chromium } from 'playwright'

const root = process.cwd()
const distDir = path.join(root, 'dist')
const outDir = path.resolve(root, '../../../..', 'out', 'release')
const reportPath = path.join(outDir, 'flow-frontend-browser-smoke.json')
const externalBaseUrl = process.env.FLYTO_RELEASE_BROWSER_SMOKE_URL
const systemBrowserCandidates = [
  process.env.FLYTO_RELEASE_BROWSER_EXECUTABLE,
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
].filter(Boolean)

const smokePaths = [
  '/my-templates',
  '/templates/builder',
  '/variables',
  '/observability/metrics',
]

function json(response, value) {
  response.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' })
  response.end(JSON.stringify(value))
}

function apiResponse(pathname) {
  if (pathname === '/api/runtime-config') {
    return { deploymentMode: 'local_offline', edition: 'ce', accountRequired: false }
  }
  if (pathname === '/api/capabilities') {
    return { edition: 'ce', deployment: 'local_offline', accountRequired: false, capabilities: [], pages: {} }
  }
  if (pathname === '/api/config/all') return { ok: true, config: { llm: { providers: [] } } }
  if (pathname === '/api/templates/' || pathname === '/api/templates') {
    return { ok: true, items: [], total: 0, page: 1, pageSize: 200, hasNext: false }
  }
  if (pathname === '/api/modules/tiered') {
    return { ok: true, default: { modules: [] }, expert: { modules: [] }, modulesMetadata: {}, moduleCategories: [] }
  }
  if (pathname.startsWith('/api/variables')) return { ok: true, items: [], variables: [] }
  if (pathname.startsWith('/api/observability') || pathname.startsWith('/api/metrics')) return { ok: true, items: [], metrics: [] }
  return { ok: true }
}

function contentType(filePath) {
  if (filePath.endsWith('.html')) return 'text/html; charset=utf-8'
  if (filePath.endsWith('.js')) return 'text/javascript; charset=utf-8'
  if (filePath.endsWith('.css')) return 'text/css; charset=utf-8'
  if (filePath.endsWith('.svg')) return 'image/svg+xml'
  if (filePath.endsWith('.png')) return 'image/png'
  if (filePath.endsWith('.woff2')) return 'font/woff2'
  return 'application/octet-stream'
}

function startServer() {
  if (!fs.existsSync(path.join(distDir, 'index.html'))) {
    throw new Error('dist/index.html is missing; run npm run build first')
  }
  const server = http.createServer((request, response) => {
    const url = new URL(request.url ?? '/', 'http://127.0.0.1')
    if (url.pathname.startsWith('/api/')) {
      json(response, apiResponse(url.pathname))
      return
    }
    const decoded = decodeURIComponent(url.pathname)
    const normalized = path.normalize(decoded).replace(/^(\.\.[/\\])+/, '')
    let filePath = path.join(distDir, normalized)
    if (!filePath.startsWith(distDir)) {
      response.writeHead(403)
      response.end('forbidden')
      return
    }
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      filePath = path.join(distDir, 'index.html')
    }
    response.writeHead(200, { 'Content-Type': contentType(filePath), 'Cache-Control': 'no-store' })
    fs.createReadStream(filePath).pipe(response)
  })
  server.on('upgrade', (_request, socket) => socket.destroy())
  return new Promise((resolve, reject) => {
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const address = server.address()
      resolve({
        baseUrl: `http://127.0.0.1:${address.port}`,
        close: () => new Promise(done => server.close(done)),
      })
    })
  })
}

const localServer = externalBaseUrl ? null : await startServer()
const baseUrl = externalBaseUrl || localServer.baseUrl
const allowedOrigin = new URL(baseUrl).origin
const systemBrowser = systemBrowserCandidates.find(candidate => fs.existsSync(candidate))
const browser = await chromium.launch({ headless: true, ...(systemBrowser ? { executablePath: systemBrowser } : {}) })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const errors = []
const outbound = []

page.on('console', message => {
  if (message.type() === 'error' && !/WebSocket/.test(message.text())) errors.push(message.text())
})
page.on('pageerror', error => errors.push(error.message))
page.on('request', request => {
  if (new URL(request.url()).origin !== allowedOrigin) outbound.push(request.url())
})

const results = []
for (const pathname of smokePaths) {
  const started = Date.now()
  await page.goto(`${baseUrl}${pathname}`, { waitUntil: 'domcontentloaded', timeout: 15000 })
  await page.waitForTimeout(250)
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  results.push({ path: pathname, url: page.url(), durationMs: Date.now() - started, horizontalOverflowPx: overflow })
  if (overflow > 2) errors.push(`${pathname}: horizontal overflow ${overflow}px`)
}

await browser.close()
if (localServer) await localServer.close()
fs.mkdirSync(outDir, { recursive: true })
fs.writeFileSync(reportPath, JSON.stringify({ project: 'flyto2-flow', baseUrl, results, errors, outbound }, null, 2))

if (outbound.length) throw new Error(`implicit outbound requests detected: ${outbound.join(', ')}`)
if (errors.length) throw new Error(`browser smoke failed: ${errors.join(' | ')}`)
console.log(`Flyto2 Flow browser smoke passed: ${reportPath}`)
