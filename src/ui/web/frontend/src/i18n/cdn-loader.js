/**
 * CDN Loader for flyto-i18n translations
 *
 * Background updater for translation hot-updates.
 * Bundled baseline translations are always available (see index.js).
 * This module fetches newer translations from CDN when available.
 *
 * CDN endpoints (tried in order):
 * 1. GitHub raw: instant updates after push (max-age=300s)
 * 2. jsDelivr: fast CDN, branch cache up to 12h
 */
import { DEFAULTS } from '@/config/defaults'

// App version for cache invalidation (new app version = fresh cache)
const APP_VERSION = import.meta.env.VITE_APP_VERSION || '0.0.0'

// CDN version/branch for GitHub-based endpoints
const I18N_VERSION = import.meta.env.VITE_I18N_VERSION || 'main'

// CDN endpoints (tried in order, first success wins)
const CDN_ENDPOINTS = [
  `https://raw.githubusercontent.com/flytohub/flyto-i18n/${I18N_VERSION}/dist`,
  `https://cdn.jsdelivr.net/gh/flytohub/flyto-i18n@${I18N_VERSION}/dist`
]

// Cache prefix includes app version - new app version = automatic cache refresh
const CACHE_PREFIX = `flyto-i18n-v${APP_VERSION}-`
const MANIFEST_TTL = DEFAULTS.CACHE_TTL.MANIFEST
const TRANSLATION_TTL = DEFAULTS.CACHE_TTL.TRANSLATION // 7 days for translations
const FETCH_TIMEOUT = DEFAULTS.TIMEOUTS.CDN_FETCH // 5 seconds per endpoint

// Scope determines which translation bundle to load
const I18N_SCOPE = import.meta.env.VITE_I18N_SCOPE || 'cloud'

// Scope-aware manifest cache key
const MANIFEST_CACHE_KEY_SCOPED = `${CACHE_PREFIX}${I18N_SCOPE}-manifest-meta`

// Will be populated from manifest - used as cache version for translations
let manifestVersion = null

// --- Fetch utilities ---

/** Fetch with an AbortController-based timeout */
async function fetchWithTimeout(url, timeout = FETCH_TIMEOUT, options = {}) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)
  try {
    const response = await fetch(url, { signal: controller.signal, ...options })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    throw error
  }
}

/** Try each CDN endpoint in order, returning the first successful JSON response */
async function fetchWithFallback(path, fetchOptions = {}) {
  for (const baseUrl of CDN_ENDPOINTS) {
    const url = `${baseUrl}${path}`
    try {
      const response = await fetchWithTimeout(url, FETCH_TIMEOUT, fetchOptions)
      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      // Try next endpoint
    }
  }
  return null
}

// --- Path helpers ---

/** Build the CDN path for a locale's translation file */
function getTranslationPath(locale) {
  if (I18N_SCOPE === 'all') return `/${locale}.json`
  return `/${I18N_SCOPE}/${locale}.json`
}

/** Build the CDN path for the manifest file */
function getManifestPath() {
  if (I18N_SCOPE === 'all') return '/manifest.json'
  return `/${I18N_SCOPE}/manifest.json`
}

// --- Public API ---

/**
 * Filter out empty string values from translations object (recursive).
 * Ensures vue-i18n fallback works correctly for untranslated keys.
 */
export function filterEmptyValues(obj) {
  if (typeof obj !== 'object' || obj === null) return obj

  const result = {}
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'object' && value !== null) {
      const filtered = filterEmptyValues(value)
      if (Object.keys(filtered).length > 0) {
        result[key] = filtered
      }
    } else if (value !== '' && value !== null && value !== undefined) {
      result[key] = value
    }
  }
  return result
}

/**
 * Check CDN for translation updates.
 * Compares CDN manifest version with bundled baseline version.
 * Returns updated translations if a newer version is available.
 *
 * @param {string} baselineVersion - Bundled baseline version string
 * @returns {Promise<{locales: object, updates: Object<string, object>}>}
 *   - locales: locale metadata from manifest (for language picker)
 *   - updates: map of locale → translations for locales that have updates
 */
export async function checkForUpdates(baselineVersion, localesToCheck = []) {
  const result = { locales: {}, updates: {} }

  try {
    // 1. Fetch manifest (check localStorage cache first)
    const cachedMeta = getManifestFromCache()
    let cdnVersion
    let localesInfo = {}

    if (cachedMeta) {
      cdnVersion = cachedMeta.version
      localesInfo = cachedMeta.locales
    } else {
      const manifest = await fetchWithFallback(getManifestPath(), { cache: 'no-cache' })
      // No manifest, or a manifest without a content-hash version, means we
      // cannot reliably tell whether the CDN differs from the bundled baseline.
      // Keep the bundled baseline rather than synthesize a fake version (e.g.
      // Date.now()), which — being a 13-char number — always sorts above the
      // 12-char content hash and would clobber the baseline on every boot.
      if (!manifest || !manifest.version) return result

      cdnVersion = manifest.version
      localesInfo = manifest.locales || {}
      setManifestToCache({ version: cdnVersion, locales: localesInfo })
    }

    manifestVersion = cdnVersion
    result.locales = localesInfo

    // 2. For each locale, check if CDN has newer translations
    for (const locale of localesToCheck) {
      const cacheKey = `${CACHE_PREFIX}${I18N_SCOPE}-${locale}-all`

      // Check localStorage cache (from a previous CDN update)
      const cached = getFromCache(cacheKey, TRANSLATION_TTL)
      if (cached) {
        result.updates[locale] = cached
        continue
      }

      // `version` is a CONTENT hash (sha256 prefix from flyto-i18n
      // build-dist.py), NOT a monotonic counter — ordering comparisons like
      // `<=` are meaningless and made updates land or not by hash byte-order
      // (the root cause of "translations very unstable"). Any difference means
      // the CDN content differs from the bundled baseline, so prefer the CDN.
      if (cdnVersion === baselineVersion) continue

      // Fetch fresh translations from CDN
      const path = getTranslationPath(locale)
      const data = await fetchWithFallback(path, { cache: 'no-cache' })
      if (data) {
        const translations = filterEmptyValues(data.translations || {})
        setToCache(cacheKey, translations)
        result.updates[locale] = translations
      }
    }
  } catch {
    // CDN unavailable — baseline stays
  }

  return result
}

/**
 * Load translations for a locale that has no bundled baseline (e.g., Japanese).
 * Used when user switches to a non-bundled locale.
 */
export async function loadTranslationsForLocale(locale) {
  const cacheKey = `${CACHE_PREFIX}${I18N_SCOPE}-${locale}-all`

  // Check localStorage cache first
  const cached = getFromCache(cacheKey, TRANSLATION_TTL)
  if (cached) return cached

  // Fetch from CDN
  const path = getTranslationPath(locale)
  const data = await fetchWithFallback(path, { cache: 'no-cache' })

  if (data) {
    const translations = filterEmptyValues(data.translations || {})
    setToCache(cacheKey, translations)
    return translations
  }

  return {}
}

/**
 * Load module translations for a specific category
 */
export async function loadModuleTranslations(locale, category) {
  const cacheKey = `${CACHE_PREFIX}${locale}-${category}`
  const cached = getFromCache(cacheKey, TRANSLATION_TTL)
  if (cached) return cached

  const data = await fetchWithFallback(`/locales/modules/${locale}/${category}.json`, { cache: 'no-cache' })
  if (data) {
    const translations = data.translations || {}
    setToCache(cacheKey, translations)
    return translations
  }
  return {}
}

/**
 * Clear all cached translations
 */
export function clearCache() {
  const keys = Object.keys(localStorage).filter((k) => k.startsWith(CACHE_PREFIX))
  keys.forEach((k) => localStorage.removeItem(k))
}

// --- Cache utilities ---

/** Read cached manifest metadata from localStorage, respecting TTL */
function getManifestFromCache() {
  try {
    const raw = localStorage.getItem(MANIFEST_CACHE_KEY_SCOPED)
    if (!raw) return null
    const { data, timestamp } = JSON.parse(raw)
    if (Date.now() - timestamp > MANIFEST_TTL) {
      localStorage.removeItem(MANIFEST_CACHE_KEY_SCOPED)
      return null
    }
    return data
  } catch {
    return null
  }
}

/** Write manifest metadata to localStorage with timestamp */
function setManifestToCache(data) {
  try {
    localStorage.setItem(
      MANIFEST_CACHE_KEY_SCOPED,
      JSON.stringify({ data, timestamp: Date.now() })
    )
  } catch {}
}

/** Read a cached value from localStorage, invalidating on TTL or version mismatch */
function getFromCache(key, ttl) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return null
    const { data, timestamp, version } = JSON.parse(raw)
    if (manifestVersion && version !== manifestVersion) {
      localStorage.removeItem(key)
      return null
    }
    if (Date.now() - timestamp > ttl) {
      localStorage.removeItem(key)
      return null
    }
    return data
  } catch {
    return null
  }
}

/** Write a value to localStorage with timestamp and manifest version */
function setToCache(key, data) {
  try {
    localStorage.setItem(
      key,
      JSON.stringify({
        data,
        timestamp: Date.now(),
        version: manifestVersion || 'unknown'
      })
    )
  } catch {}
}

export default {
  checkForUpdates,
  loadTranslationsForLocale,
  loadModuleTranslations,
  filterEmptyValues,
  clearCache
}
