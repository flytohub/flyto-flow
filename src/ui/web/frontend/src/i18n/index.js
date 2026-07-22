/** Bundled-only CE translations. This module never accesses a CDN. */
import { createI18n } from 'vue-i18n'
import { localOverrides, deepMerge } from './local-overrides'
import localeManifest from './bundled/manifest.json'

const STORAGE_KEY = 'app_locale'
const bundledLocaleModules = import.meta.glob('./bundled/*.json')
const LOCALES = Object.fromEntries(
  Object.entries(localeManifest.locales)
    .map(([code, metadata]) => [code, {
      ...metadata,
      load: bundledLocaleModules[`./bundled/${code}.json`],
    }])
    .filter(([, metadata]) => typeof metadata.load === 'function')
)

function detectLocale() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved && LOCALES[saved]) return saved
  const browser = navigator.language || 'en'
  if (browser.startsWith('zh-CN') || browser.startsWith('zh-Hans')) return 'zh-CN'
  if (browser.startsWith('zh')) return 'zh-TW'
  return 'en'
}

function withoutEmptyValues(value) {
  if (Array.isArray(value)) return value.map(withoutEmptyValues)
  if (!value || typeof value !== 'object') return value
  return Object.fromEntries(Object.entries(value)
    .filter(([, item]) => item !== '')
    .map(([key, item]) => [key, withoutEmptyValues(item)]))
}

const i18n = createI18n({
  legacy: false,
  locale: detectLocale(),
  fallbackLocale: 'en',
  messages: {},
  globalInjection: true,
  missingWarn: import.meta.env.DEV,
  fallbackWarn: import.meta.env.DEV
})

async function loadLocale(locale) {
  const selected = LOCALES[locale] ? locale : 'en'
  if (Object.keys(i18n.global.getLocaleMessage(selected)).length) return selected
  const module = await LOCALES[selected].load()
  const payload = module.default || module
  const bundled = withoutEmptyValues(payload.translations || {})
  i18n.global.setLocaleMessage(selected, deepMerge(bundled, localOverrides[selected] || {}))
  return selected
}

export async function initI18n() {
  await loadLocale('en')
  const locale = await loadLocale(detectLocale())
  i18n.global.locale.value = locale
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.setAttribute('lang', locale)
}

export async function setLocale(locale) {
  const selected = await loadLocale(locale)
  i18n.global.locale.value = selected
  localStorage.setItem(STORAGE_KEY, selected)
  document.documentElement.setAttribute('lang', selected)
}

export function getLocale() { return i18n.global.locale.value }
export function getAvailableLocales() {
  return Object.entries(LOCALES).map(([code, value]) => ({ code, ...value, completion: 100 }))
}

document.documentElement.setAttribute('lang', detectLocale())
export default i18n
