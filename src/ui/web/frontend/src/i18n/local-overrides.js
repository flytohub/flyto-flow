/**
 * Local translation overrides
 *
 * These are merged with CDN translations.
 * Use ONLY for temporary overrides before CDN is updated.
 *
 * All translations should live in flyto-i18n repo.
 * After CDN is updated, remove entries from here.
 */

export const localOverrides = {
  en: {},
  'zh-TW': {}
}

/**
 * Deep merge helper
 */
export function deepMerge(target, source) {
  const result = { ...target }
  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = deepMerge(result[key] || {}, source[key])
    } else {
      result[key] = source[key]
    }
  }
  return result
}
