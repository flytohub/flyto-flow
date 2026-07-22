/** Optional overrides layered onto the translation files bundled in this build. */

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
