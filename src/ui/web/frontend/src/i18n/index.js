/**
 * i18n Configuration
 *
 * Bundled baseline translations load instantly (zero network dependency).
 * CDN hot-update runs in background to pick up newer translations.
 */

import { createI18n } from 'vue-i18n'
import { shallowRef } from 'vue'
import {
  checkForUpdates,
  loadTranslationsForLocale,
  filterEmptyValues
} from './cdn-loader'
import { localOverrides, deepMerge } from './local-overrides'

// Bundled baseline translations (committed to repo, always available).
// Load them on demand so the app entry chunk does not embed every locale JSON.
const BUNDLED_LOADERS = {
  en: () => import('./bundled/en.json'),
  'zh-TW': () => import('./bundled/zh-TW.json'),
  'zh-CN': () => import('./bundled/zh-CN.json')
}
const BUNDLED_LOCALES = new Set(Object.keys(BUNDLED_LOADERS))
const loadedBundledData = {}
let bundledVersion = null

/**
 * Stable-stringify a messages object for cheap content comparison.
 * Keys are sorted recursively so two structurally-identical objects with
 * different insertion order produce the same string. Used to skip redundant
 * setLocaleMessage calls (which trigger a reactive re-render / string flicker)
 * when the CDN-merged content is identical to what's already mounted.
 */
function stableStringify(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`
  const keys = Object.keys(value).sort()
  return `{${keys.map(k => `${JSON.stringify(k)}:${stableStringify(value[k])}`).join(',')}}`
}

/** True when two messages objects are structurally equal (order-insensitive). */
function messagesEqual(a, b) {
  if (a === b) return true
  if (!a || !b) return false
  return stableStringify(a) === stableStringify(b)
}

/** Flatten nested translation object to dot-separated keys (for stale-key comparison) */
function flattenKeys(obj, prefix = '') {
  const result = {}
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    if (typeof value === 'object' && value !== null) {
      Object.assign(result, flattenKeys(value, fullKey))
    } else {
      result[fullKey] = value
    }
  }
  return result
}

const STORAGE_KEY = 'app_locale'
const DEFAULT_LOCALES = ['en', 'zh-TW', 'zh-CN', 'ja', 'ko', 'fr', 'es', 'hi']

// Will be populated from CDN manifest
let supportedLocales = [...DEFAULT_LOCALES]

// One-time guard so the "fell back to English" notice is surfaced at most once.
let notifiedLocaleFallback = false

function detectBrowserLocale() {
  const browserLang = navigator.language || navigator.userLanguage || 'en'

  if (supportedLocales.includes(browserLang)) return browserLang
  if (browserLang.startsWith('zh-CN') || browserLang.startsWith('zh-Hans') || browserLang === 'zh') return 'zh-CN'
  if (browserLang.startsWith('zh')) return 'zh-TW'

  const langPrefix = browserLang.split('-')[0]
  if (supportedLocales.includes(langPrefix)) return langPrefix

  return 'en'
}

function getSavedLocale() {
  return localStorage.getItem(STORAGE_KEY)
}

function getDefaultLocale() {
  const saved = getSavedLocale()
  if (saved && DEFAULT_LOCALES.includes(saved)) return saved
  if (saved) return saved
  return detectBrowserLocale()
}

const bundledMessages = {}

function isBundledLocale(locale) {
  return BUNDLED_LOCALES.has(locale)
}

async function loadBundledData(locale) {
  if (!isBundledLocale(locale)) return null
  if (loadedBundledData[locale]) return loadedBundledData[locale]

  const module = await BUNDLED_LOADERS[locale]()
  const data = module.default || module
  loadedBundledData[locale] = data
  bundledMessages[locale] = filterEmptyValues(data.translations || {})
  if (locale === 'en') {
    bundledVersion = data.version || bundledVersion
  }
  return data
}

async function ensureBundledLocale(locale) {
  const data = await loadBundledData(locale)
  if (!data) return false

  const merged = deepMerge(bundledMessages[locale] || {}, localOverrides[locale] || {})
  if (!messagesEqual(i18n.global.getLocaleMessage(locale), merged)) {
    i18n.global.setLocaleMessage(locale, merged)
  }
  return true
}

/**
 * Create i18n instance with bundled baseline messages
 */
const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'en',
  messages: {},
  globalInjection: true,
  // Warn about missing/fallback keys in dev so typo'd keys (which otherwise
  // render the raw key name) are caught; stay silent in production.
  missingWarn: import.meta.env.DEV,
  fallbackWarn: import.meta.env.DEV
})

// Fallback region mapping for common locales. Keep this in sync with the
// SVGs under public/flags/ and the locales declared in flyto-i18n's
// dist/cloud/manifest.json — anything missing here renders as a globe.
const LOCALE_REGION_MAP = {
  en: 'US', 'en-US': 'US', 'en-GB': 'GB',
  zh: 'TW', 'zh-TW': 'TW', 'zh-CN': 'CN',
  ja: 'JP', ko: 'KR', fr: 'FR', de: 'DE',
  es: 'ES', it: 'IT', pt: 'PT', 'pt-BR': 'BR', ru: 'RU', hi: 'IN',
  id: 'ID', pl: 'PL', th: 'TH', tr: 'TR', vi: 'VN'
}

function getRegionForLocale(code, infoRegion) {
  if (infoRegion && infoRegion.length === 2) return infoRegion.toUpperCase()
  if (LOCALE_REGION_MAP[code]) return LOCALE_REGION_MAP[code]

  const parts = code.split('-')
  if (parts.length > 1) {
    const regionPart = parts[parts.length - 1]
    if (regionPart.length === 2) return regionPart.toUpperCase()
  }
  if (LOCALE_REGION_MAP[parts[0]]) return LOCALE_REGION_MAP[parts[0]]
  return null
}

/**
 * Apply locale info from CDN manifest
 */
function applyLocalesInfo(localesInfo) {
  if (Object.keys(localesInfo).length === 0) return

  supportedLocales = Object.keys(localesInfo)
  cachedLocaleInfo.value = Object.entries(localesInfo).map(([code, info]) => ({
    code,
    name: info.name || code,
    native: info.native || code,
    region: getRegionForLocale(code, info.region),
    completion: info.completion || 0
  }))
}

/**
 * Initialize i18n.
 *
 * Bundled baseline is already set in createI18n (instant, zero delay).
 * This function sets the correct locale and kicks off background CDN update.
 */
export async function initI18n() {
  await ensureBundledLocale('en')

  const savedLocale = getSavedLocale()
  let targetLocale = savedLocale || detectBrowserLocale()

  // Validate target locale: if not bundled and not in default list, fallback
  if (!isBundledLocale(targetLocale) && !DEFAULT_LOCALES.includes(targetLocale)) {
    targetLocale = detectBrowserLocale()
  }

  if (isBundledLocale(targetLocale)) {
    await ensureBundledLocale(targetLocale)
  }

  // Non-bundled locales (ja/ko/fr/es/hi etc.) have no baseline in `messages`,
  // so flipping to them immediately would render English (or get stuck on
  // English when the content-hash version gate skips the background fetch).
  // For these, fetch the translations ONCE before flipping the active locale.
  // loadTranslationsForLocale is NOT version-gated and carries its own ~5s
  // CDN_FETCH timeout, so on a slow/offline CDN it resolves empty and we fall
  // back to 'en' deterministically rather than showing a half-translated page.
  if (!isBundledLocale(targetLocale)) {
    try {
      const translations = await loadTranslationsForLocale(targetLocale)
      if (translations && Object.keys(translations).length > 0) {
        const merged = deepMerge(translations, localOverrides[targetLocale] || {})
        i18n.global.setLocaleMessage(targetLocale, merged)
      } else {
        // CDN timed out or returned nothing — fall back to English deterministically.
        if (!notifiedLocaleFallback) {
          notifiedLocaleFallback = true
          console.warn(
            `[i18n] No translations available for "${targetLocale}" (CDN unavailable); falling back to English.`
          )
        }
        targetLocale = 'en'
      }
    } catch {
      if (!notifiedLocaleFallback) {
        notifiedLocaleFallback = true
        console.warn(
          `[i18n] Failed to load translations for "${targetLocale}"; falling back to English.`
        )
      }
      targetLocale = 'en'
    }
  }

  // Set locale (bundled messages are already loaded for en/zh-TW)
  i18n.global.locale.value = targetLocale
  localStorage.setItem(STORAGE_KEY, targetLocale)
  document.documentElement.setAttribute('lang', targetLocale)

  // Background: check CDN for newer translations (non-blocking)
  const localesToUpdate = targetLocale !== 'en'
    ? [targetLocale, 'en']
    : ['en']

  updateFromCDN(targetLocale, localesToUpdate, bundledVersion)
}

/**
 * Background CDN update — fetch newer translations if available.
 * Runs after app is already rendered with bundled baseline.
 */
async function updateFromCDN(targetLocale, localesToUpdate, baselineVersion) {
  try {
    const { locales, updates } = await checkForUpdates(baselineVersion, localesToUpdate)

    // Update locale metadata (for language picker)
    applyLocalesInfo(locales)

    // Validate target locale against CDN manifest
    if (Object.keys(locales).length > 0 && !supportedLocales.includes(targetLocale)) {
      targetLocale = detectBrowserLocale()
      i18n.global.locale.value = targetLocale
      localStorage.setItem(STORAGE_KEY, targetLocale)
    }

    // Hot-swap translations if CDN has newer versions
    // Merge: bundled baseline → CDN updates → local overrides
    // CDN overrides bundled keys but doesn't wipe missing keys
    for (const [locale, translations] of Object.entries(updates)) {
      const baseline = bundledMessages[locale] || {}
      const merged = deepMerge(deepMerge(baseline, translations), localOverrides[locale] || {})
      // Only hot-swap when the merged content actually differs from what's
      // mounted. setLocaleMessage is reactive, so re-setting identical content
      // forces a re-render and causes a visible string flicker on first paint.
      if (!messagesEqual(i18n.global.getLocaleMessage(locale), merged)) {
        i18n.global.setLocaleMessage(locale, merged)
      }

      // Stale-key detection (dev only): warn when bundled baseline has keys
      // that the CDN no longer provides — signals flyto-i18n deleted them
      // but the bundled baseline hasn't been synced yet.
      if (import.meta.env.DEV && locale === 'en' && bundledMessages[locale]) {
        const flatCDN = flattenKeys(translations)
        const flatBundled = flattenKeys(bundledMessages[locale])
        const staleKeys = Object.keys(flatBundled).filter(k => !(k in flatCDN))
        if (staleKeys.length > 0) {
          console.warn(
            `[i18n] ${staleKeys.length} stale key(s) in bundled baseline (deleted from CDN):`,
            staleKeys.slice(0, 10)
          )
        }
      }
    }

    // If target locale has no bundled baseline and CDN didn't provide it, fetch it
    if (!isBundledLocale(targetLocale) && !updates[targetLocale]) {
      const translations = await loadTranslationsForLocale(targetLocale)
      if (Object.keys(translations).length > 0) {
        const merged = deepMerge(translations, localOverrides[targetLocale] || {})
        if (!messagesEqual(i18n.global.getLocaleMessage(targetLocale), merged)) {
          i18n.global.setLocaleMessage(targetLocale, merged)
        }
      }
    }

    // Sync module translations to backend (for module label translation)
    syncModuleTranslationsToBackend(targetLocale)
  } catch {
    // CDN unavailable — bundled baseline is already active
    // Still sync bundled translations to backend
    syncModuleTranslationsToBackend(targetLocale)
  }
}

/**
 * Set locale and save to localStorage.
 * For non-bundled locales, fetches from CDN.
 */
export async function setLocale(locale) {
  if (!supportedLocales.includes(locale)) return

  // Load translations if not already loaded
  const currentMessages = i18n.global.getLocaleMessage(locale)
  if (!currentMessages || Object.keys(currentMessages).length === 0) {
    if (isBundledLocale(locale)) {
      await ensureBundledLocale(locale)
    } else {
      const translations = await loadTranslationsForLocale(locale)
      if (Object.keys(translations).length > 0) {
        const merged = deepMerge(translations, localOverrides[locale] || {})
        i18n.global.setLocaleMessage(locale, merged)
      }
    }
  }

  i18n.global.locale.value = locale
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.setAttribute('lang', locale)

  syncModuleTranslationsToBackend(locale)
}

/**
 * Get current locale
 */
export function getLocale() {
  return i18n.global.locale.value
}

// Cached locale info from manifest. shallowRef so consumers reading it
// inside a computed/render get an automatic re-evaluation once the CDN
// manifest lands — without this the LanguageSwitcher dropdown is stuck
// on DEFAULT_LOCALES (8 entries) even after the 16-locale manifest
// finishes downloading.
const cachedLocaleInfo = shallowRef(null)

/**
 * Get available locales with metadata (synchronous, reactive).
 * Reading this inside a computed creates a dep on cachedLocaleInfo —
 * the dep fires when CDN updates the manifest, so the dropdown grows
 * from the 8-entry fallback to whatever the manifest declares.
 */
export function getAvailableLocales() {
  if (cachedLocaleInfo.value) return cachedLocaleInfo.value

  // Fallback before manifest is loaded
  return DEFAULT_LOCALES.map(code => ({
    code,
    name: LOCALE_REGION_MAP[code] ? code : code,
    native: code,
    region: LOCALE_REGION_MAP[code] || null,
    completion: code === 'en' ? 100 : 0
  }))
}

/**
 * Sync modules.* translation keys to backend for module label translation.
 * Fire-and-forget — failure is silent (backend falls back to bundled files).
 */
function syncModuleTranslationsToBackend(locale) {
  try {
    const messages = i18n.global.getLocaleMessage(locale)
    if (!messages || typeof messages !== 'object') return

    const moduleKeys = {}
    for (const [key, value] of Object.entries(messages)) {
      if (key.startsWith('modules.') && typeof value === 'string') {
        moduleKeys[key] = value
      }
    }

    if (Object.keys(moduleKeys).length === 0) return

    import('@/api/client').then(({ post }) => {
      post('/i18n/sync', { locale, translations: moduleKeys }).catch(() => {})
    }).catch(() => {})
  } catch {
    // Silent — backend uses bundled files as fallback
  }
}

// Set initial HTML lang attribute
document.documentElement.setAttribute('lang', getDefaultLocale())

export default i18n
