import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import i18n, { initI18n } from './i18n'
import App from './App.vue'
import 'virtual:uno.css'
import '@unocss/reset/tailwind.css'
import './style.css'

import { initClient } from './api/client'
// Initialize plugin system
import { initPlugins } from './plugins/init'
// Telemetry service for error tracking
import { telemetry, initTelemetryErrorHandlers } from './services/telemetry'

// Handle chunk load failures after frontend hot update.
// When hot updater replaces dist/ files, old chunk filenames become 404.
// Auto-reload once so the new entry point references correct chunk hashes.
window.addEventListener('vite:preloadError', () => {
  const reloadKey = 'flyto-chunk-reload'
  if (!sessionStorage.getItem(reloadKey)) {
    sessionStorage.setItem(reloadKey, '1')
    window.location.reload()
  }
})

// Tag the root element with the OS so CSS can ship per-platform fallbacks
// for features that render poorly on WebView2 (mask-composite, heavy
// drop-shadow stacks, fractional-DPI 1px borders). Done before mount so
// styles apply on the very first paint.
function tagPlatform() {
  const ua = navigator.userAgentData?.platform || navigator.userAgent || ''
  const cls = /win/i.test(ua)
    ? 'is-windows'
    : /mac/i.test(ua)
    ? 'is-mac'
    : /linux/i.test(ua)
    ? 'is-linux'
    : 'is-other'
  document.documentElement.classList.add(cls)
}

async function bootstrap() {
  tagPlatform()
  await initClient()

  // Initialize i18n (loads CDN translations in CDN_ONLY mode)
  await initI18n()

  // Initialize plugin system (field renderers, etc.)
  await initPlugins()

  // Initialize global error handlers for telemetry
  initTelemetryErrorHandlers()

  const app = createApp(App)

  // Global error handler for Vue errors
  app.config.errorHandler = (err, instance, info) => {

    // Track Vue errors via telemetry
    telemetry.trackVueError(err, instance, info)
  }


  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(i18n)

  // Initialize auth BEFORE mount so router guard doesn't hang waiting for
  // authInitialized. Without this, the first beforeEach fires before
  // App.vue onMounted, causing waitForAuth() to poll indefinitely.
  // init() restores user from localStorage (sync) and kicks off initAuth()
  // which validates the token via /auth/me; authInitialized flips to true
  // only after that resolves so waitForAuth() never reports "ready" with
  // an unset user.
  try {
    const { useUserStore } = await import('./stores/userStore')
    useUserStore().init()
  } catch {
    // Auth init failed — router guard will redirect to /login
  }

  app.mount('#app')
}

bootstrap()
