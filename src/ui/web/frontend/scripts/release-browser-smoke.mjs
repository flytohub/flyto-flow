import fs from 'node:fs'
import http from 'node:http'
import path from 'node:path'
import { chromium } from 'playwright'

const root = process.cwd()
const distDir = path.join(root, 'dist')
const outDir = path.resolve(root, '../../../..', 'out', 'release')
const reportPath = path.join(outDir, 'cloud-frontend-browser-smoke.json')
const externalBaseUrl = process.env.FLYTO_RELEASE_BROWSER_SMOKE_URL
const authEmail = process.env.FLYTO_RELEASE_AUTH_EMAIL
const authPassword = process.env.FLYTO_RELEASE_AUTH_PASSWORD
const freeTemplateId = process.env.FLYTO_RELEASE_FREE_TEMPLATE_ID
const paidTemplateId = process.env.FLYTO_RELEASE_PAID_TEMPLATE_ID
const perCallTemplateId = process.env.FLYTO_RELEASE_PER_CALL_TEMPLATE_ID

const budgets = {
  localNavigationMs: 8000,
  externalNavigationMs: 15000,
  maxHorizontalOverflowPx: 2,
}

const smokePaths = [
  { id: 'home', path: '/', expectedUrl: /./ },
  { id: 'login', path: '/login', expectedUrl: /login|auth|\/$/ },
  { id: 'privacy', path: '/privacy', expectedUrl: /privacy/ },
  { id: 'terms', path: '/terms', expectedUrl: /terms/ },
  { id: 'marketplace-public-data-boundary', path: '/marketplace', expectedUrl: /marketplace/, dataBoundary: true },
  { id: 'dashboard-protected', path: '/dashboard', expectedUrl: /dashboard|login|auth/ },
]

const authenticatedSmokePaths = [
  { id: 'dashboard-authenticated', path: '/dashboard', expectedUrl: /dashboard/, dataBoundary: true },
  { id: 'my-templates-authenticated', path: '/my-templates', expectedUrl: /my-templates|workflows/, dataBoundary: true },
  { id: 'builder-authenticated', path: '/templates/builder', expectedUrl: /templates\/builder/, dataBoundary: true },
  { id: 'marketplace-authenticated', path: '/marketplace', expectedUrl: /marketplace/, dataBoundary: true },
]

function fail(message) {
  throw new Error(message)
}

function contentType(filePath) {
  if (filePath.endsWith('.html')) return 'text/html; charset=utf-8'
  if (filePath.endsWith('.js')) return 'text/javascript; charset=utf-8'
  if (filePath.endsWith('.css')) return 'text/css; charset=utf-8'
  if (filePath.endsWith('.svg')) return 'image/svg+xml'
  if (filePath.endsWith('.png')) return 'image/png'
  if (filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) return 'image/jpeg'
  if (filePath.endsWith('.webp')) return 'image/webp'
  if (filePath.endsWith('.woff2')) return 'font/woff2'
  return 'application/octet-stream'
}

function writeJson(response, status, data) {
  response.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
  })
  response.end(JSON.stringify(data))
}

function startStaticServer() {
  if (!fs.existsSync(path.join(distDir, 'index.html'))) {
    fail('dist/index.html is missing. Run npm run build before release:browser-smoke.')
  }

  const server = http.createServer((request, response) => {
    const url = new URL(request.url ?? '/', 'http://127.0.0.1')
    if (url.pathname === '/api/health') {
      writeJson(response, 200, { ok: true, status: 'ok' })
      return
    }
    if (url.pathname === '/api/encryption/public-key') {
      writeJson(response, 200, { ok: true, enabled: false })
      return
    }
    if (url.pathname === '/api/telemetry') {
      writeJson(response, 200, { ok: true })
      return
    }
    if (url.pathname === '/api/auth/config') {
      writeJson(response, 200, { ok: true, providers: [] })
      return
    }
    if (url.pathname === '/api/config/all') {
      writeJson(response, 200, { ok: true, config: {} })
      return
    }
    if (url.pathname === '/api/capabilities') {
      writeJson(response, 200, {
        ok: true,
        deploymentMode: 'saas_cloud',
        licenseType: 'free',
        isLicensed: false,
        isPro: false,
        isAdmin: false,
        capabilities: [],
        features: {},
        pages: {},
        ui: {
          showMarketplace: true,
          showBilling: true,
          allowSelfSignup: true,
          authMethod: 'firebase',
          canUpgrade: true,
        },
      })
      return
    }
    if (url.pathname === '/api/auth/me') {
      writeJson(response, 401, { ok: false, error: 'unauthenticated' })
      return
    }
    if (url.pathname === '/api/modules/tiered') {
      writeJson(response, 200, {
        ok: true,
        default: { modules: null },
        expert: null,
        modules_metadata: { 'browser.goto': { moduleId: 'browser.goto', label: 'Go to URL' } },
        module_categories: 'bad-shape',
      })
      return
    }
    if (url.pathname === '/api/templates/search') {
      writeJson(response, 200, {
        ok: true,
        templates: [
          null,
          'bad-template',
          {
            id: 'tpl-smoke',
            name: 'Smoke Template',
            category: 'automation',
            creator_id: null,
            downloads: 'bad-count',
          },
        ],
        total: 'bad-total',
      })
      return
    }
    if (url.pathname === '/api/templates/categories') {
      writeJson(response, 200, {
        ok: true,
        categories: [null, { id: 'automation', slug: 'automation', name: 'Automation' }],
      })
      return
    }
    if (url.pathname === '/api/templates/library') {
      writeJson(response, 200, { ok: true, items: [null, 'bad-library-item'] })
      return
    }
    if (url.pathname === '/api/templates/me/templates') {
      writeJson(response, 200, {
        ok: true,
        templates: [null, { id: 'my-template-smoke', name: 'My Template Smoke' }],
        total: 'bad-total',
        has_next: false,
      })
      return
    }
    if (url.pathname === '/api/templates/folders/' || url.pathname === '/api/templates/folders') {
      writeJson(response, 200, {
        ok: true,
        folders: [null, { id: 'folder-smoke', name: null, parent_id: null, direct_count: 'bad' }],
        default_position: 'bad',
        default_count: 'bad',
        total_count: 1,
      })
      return
    }
    if (url.pathname === '/api/recipe-bundles/public') {
      writeJson(response, 200, { ok: true, bundles: null })
      return
    }

    const decoded = decodeURIComponent(url.pathname)
    const safePath = path.normalize(decoded).replace(/^(\.\.[/\\])+/, '')
    let filePath = path.join(distDir, safePath)

    if (!filePath.startsWith(distDir)) {
      response.writeHead(403)
      response.end('forbidden')
      return
    }
    if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
      filePath = path.join(filePath, 'index.html')
    }
    if (!fs.existsSync(filePath)) {
      filePath = path.join(distDir, 'index.html')
    }

    response.writeHead(200, {
      'Content-Type': contentType(filePath),
      'Cache-Control': 'no-store',
    })
    fs.createReadStream(filePath).pipe(response)
  })
  server.on('upgrade', (_request, socket) => {
    socket.write('HTTP/1.1 426 Upgrade Required\r\nConnection: close\r\n\r\n')
    socket.destroy()
  })

  return new Promise((resolve, reject) => {
    server.on('error', reject)
    server.listen(0, '127.0.0.1', () => {
      const address = server.address()
      resolve({
        baseUrl: `http://127.0.0.1:${address.port}`,
        close: () => new Promise((closeResolve) => server.close(closeResolve)),
      })
    })
  })
}

async function maybeLogin(page, baseUrl) {
  if (!authEmail || !authPassword) {
    return { attempted: false, ok: null, reason: 'FLYTO_RELEASE_AUTH_EMAIL/PASSWORD not set' }
  }

  await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded', timeout: budgets.externalNavigationMs })
  const email = page.locator('input[type="email"], input[name="email"], input[autocomplete="email"]').first()
  const password = page.locator('input[type="password"], input[name="password"], input[autocomplete="current-password"]').first()
  if ((await email.count()) === 0 || (await password.count()) === 0) {
    return { attempted: true, ok: false, reason: 'login form selectors not found' }
  }

  await email.fill(authEmail)
  await password.fill(authPassword)
  await page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in"), button:has-text("Login")').first().click()
  await page.waitForLoadState('networkidle', { timeout: budgets.externalNavigationMs }).catch(() => undefined)
  const url = page.url()
  return {
    attempted: true,
    ok: !/\/login|\/auth/.test(url),
    reason: /\/login|\/auth/.test(url) ? 'still on auth route after login attempt' : 'authenticated route reached',
  }
}

async function inspectPath(page, baseUrl, check, observed) {
  const consoleErrors = []
  const pageErrors = []
  const failedRequests = []
  const badResponses = []
  const onConsole = (message) => {
    if (message.type() === 'error') {
      const text = message.text()
      const localOnlyAllowed =
        !externalBaseUrl && /WebSocket connection .*\/ws\/breakpoints/.test(text)
      if (!localOnlyAllowed && !/favicon|manifest|Failed to load resource: the server responded with a status of 404/.test(text)) {
        consoleErrors.push(text)
      }
    }
  }
  const onPageError = (error) => pageErrors.push(error.message)
  const onRequestFailed = (request) => {
    const resourceType = request.resourceType()
    if (['document', 'script', 'stylesheet'].includes(resourceType)) {
      failedRequests.push(`${request.method()} ${request.url()} ${request.failure()?.errorText ?? ''}`.trim())
    }
  }
  const onResponse = (response) => {
    const request = response.request()
    const resourceType = request.resourceType()
    if (response.status() >= 500 && ['document', 'script', 'stylesheet', 'xhr', 'fetch'].includes(resourceType)) {
      badResponses.push(`${response.status()} ${request.method()} ${response.url()}`)
    }
  }

  page.on('console', onConsole)
  page.on('pageerror', onPageError)
  page.on('requestfailed', onRequestFailed)
  page.on('response', onResponse)

  const started = Date.now()
  await page.goto(`${baseUrl}${check.path}`, { waitUntil: 'domcontentloaded', timeout: budgets.externalNavigationMs })
  await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => undefined)
  await page.locator('body').waitFor({ state: 'visible', timeout: 5000 })
  const durationMs = Date.now() - started
  const url = page.url()
  const metrics = await page.evaluate(() => {
    const bodyText = document.body?.innerText?.trim() ?? ''
    const navigation = performance.getEntriesByType('navigation')[0]
    return {
      title: document.title,
      url: location.href,
      bodyTextLength: bodyText.length,
      viewportWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      navigationDurationMs: navigation ? Math.round(navigation.duration) : null,
      domContentLoadedMs: navigation ? Math.round(navigation.domContentLoadedEventEnd) : null,
      resourceCount: performance.getEntriesByType('resource').length,
      hasErrorBoundary: Boolean(document.querySelector('.error-boundary')) ||
        /something went wrong|unexpected error|technical details/i.test(bodyText),
    }
  })

  page.off('console', onConsole)
  page.off('pageerror', onPageError)
  page.off('requestfailed', onRequestFailed)
  page.off('response', onResponse)

  const violations = []
  if (!check.expectedUrl.test(url)) {
    violations.push(`unexpected final URL: ${url}`)
  }
  if (metrics.bodyTextLength === 0) {
    violations.push('body has no visible text')
  }
  if (metrics.hasErrorBoundary) {
    violations.push('ErrorBoundary rendered')
  }
  const overflowPx = metrics.scrollWidth - metrics.viewportWidth
  if (overflowPx > budgets.maxHorizontalOverflowPx) {
    violations.push(`horizontal overflow ${overflowPx}px`)
  }
  if (durationMs > (externalBaseUrl ? budgets.externalNavigationMs : budgets.localNavigationMs)) {
    violations.push(`navigation took ${durationMs}ms`)
  }
  violations.push(...consoleErrors.map((value) => `console error: ${value}`))
  violations.push(...pageErrors.map((value) => `page error: ${value}`))
  violations.push(...failedRequests.map((value) => `failed request: ${value}`))
  violations.push(...badResponses.map((value) => `bad response: ${value}`))

  const result = {
    id: check.id,
    path: check.path,
    finalUrl: url,
    durationMs,
    metrics,
    consoleErrors,
    pageErrors,
    failedRequests,
    badResponses,
    violations,
    ok: violations.length === 0,
  }
  observed.push(result)
  return result
}

async function main() {
  const server = externalBaseUrl ? null : await startStaticServer()
  const baseUrl = externalBaseUrl ?? server.baseUrl
  const observed = []
  const failures = []
  let browser

  try {
    browser = await chromium.launch({ headless: true })
    const page = await browser.newPage({ viewport: { width: 1366, height: 900 } })
    const auth = await maybeLogin(page, baseUrl)
    if (auth.attempted && auth.ok === false) {
      failures.push(`auth: ${auth.reason}`)
    }

    for (const check of smokePaths) {
      const result = await inspectPath(page, baseUrl, check, observed)
      if (!result.ok) {
        failures.push(`${check.id}: ${result.violations.join('; ')}`)
      }
    }

    if (auth.ok === true) {
      for (const check of authenticatedSmokePaths) {
        const result = await inspectPath(page, baseUrl, check, observed)
        if (!result.ok) {
          failures.push(`${check.id}: ${result.violations.join('; ')}`)
        }
      }
    } else {
      for (const check of authenticatedSmokePaths) {
        observed.push({
          id: check.id,
          path: check.path,
          skipped: true,
          reason: 'authenticated smoke requires successful login',
          dataBoundary: Boolean(check.dataBoundary),
          ok: null,
          violations: [],
        })
      }
    }

    const report = {
      project: 'flyto-cloud',
      surface: 'web-frontend',
      generatedAt: new Date().toISOString(),
      mode: externalBaseUrl ? 'external-url' : 'local-dist',
      baseUrl: externalBaseUrl ? baseUrl : 'local-dist-server',
      budgets,
      auth: {
        envProvided: Boolean(authEmail && authPassword),
        attempted: auth.attempted,
        ok: auth.ok,
        reason: auth.reason,
      },
      stagingTargets: {
        freeTemplateIdProvided: Boolean(freeTemplateId),
        paidTemplateIdProvided: Boolean(paidTemplateId),
        perCallTemplateIdProvided: Boolean(perCallTemplateId),
      },
      dataBoundary: {
        errorBoundaryBlocked: true,
        authenticatedPaths: authenticatedSmokePaths.map(path => path.id),
        localMalformedFixtures: externalBaseUrl ? [] : [
          '/api/modules/tiered',
          '/api/templates/search',
          '/api/templates/categories',
          '/api/templates/library',
          '/api/templates/me/templates',
          '/api/templates/folders/',
          '/api/recipe-bundles/public',
        ],
      },
      paths: observed,
      failureCount: failures.length,
      failures,
    }

    fs.mkdirSync(outDir, { recursive: true })
    fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`)

    if (failures.length > 0) {
      console.error(`Release browser smoke failed. Report: ${reportPath}`)
      for (const failure of failures) {
        console.error(`- ${failure}`)
      }
      process.exit(1)
    }
    console.log(`Release browser smoke passed: ${observed.length} paths. Report: ${reportPath}`)
  } finally {
    if (browser) {
      await browser.close()
    }
    if (server) {
      await server.close()
    }
  }
}

main().catch((error) => {
  console.error(error?.message ?? error)
  if (/Executable doesn't exist|browserType.launch/.test(error?.message ?? '')) {
    console.error('Install Chromium with: npx playwright install chromium')
  }
  process.exit(1)
})
