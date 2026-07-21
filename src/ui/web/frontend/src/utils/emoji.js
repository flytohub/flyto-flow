/**
 * Emoji Utilities
 *
 * S-Grade: Centralized emoji functions to eliminate hardcoding.
 */

/**
 * Unicode offset for regional indicator symbols (flag emoji)
 * Regional Indicator Symbol 'A' starts at U+1F1E6 (127462)
 * Character 'A' is at code point 65
 * Offset = 127462 - 65 = 127397
 */
const REGIONAL_INDICATOR_OFFSET = 127397

/**
 * Convert a 2-letter region code to flag emoji
 *
 * @param {string} region - 2-letter ISO country code (e.g., 'US', 'TW', 'JP')
 * @param {string} fallback - Fallback emoji if region is invalid (default: globe)
 * @returns {string} Flag emoji or fallback
 *
 * @example
 * regionToFlag('US') // '🇺🇸'
 * regionToFlag('TW') // '🇹🇼'
 * regionToFlag('invalid') // '🌐'
 */
export function regionToFlag(region, fallback = '🌐') {
  if (!region || typeof region !== 'string' || region.length !== 2) {
    return fallback
  }

  const upperRegion = region.toUpperCase()

  // Validate characters are A-Z
  const charA = upperRegion.charCodeAt(0)
  const charB = upperRegion.charCodeAt(1)
  if (charA < 65 || charA > 90 || charB < 65 || charB > 90) {
    return fallback
  }

  return String.fromCodePoint(
    charA + REGIONAL_INDICATOR_OFFSET,
    charB + REGIONAL_INDICATOR_OFFSET
  )
}

/**
 * Common locale to region mapping
 */
const LOCALE_TO_REGION = {
  en: 'US',
  'en-US': 'US',
  'en-GB': 'GB',
  'en-AU': 'AU',
  zh: 'TW',
  'zh-TW': 'TW',
  'zh-CN': 'CN',
  'zh-HK': 'HK',
  ja: 'JP',
  'ja-JP': 'JP',
  ko: 'KR',
  'ko-KR': 'KR',
  fr: 'FR',
  'fr-FR': 'FR',
  de: 'DE',
  'de-DE': 'DE',
  es: 'ES',
  'es-ES': 'ES',
  it: 'IT',
  'it-IT': 'IT',
  pt: 'PT',
  'pt-BR': 'BR',
  'pt-PT': 'PT',
  ru: 'RU',
  'ru-RU': 'RU'
}

/**
 * Convert locale code to flag emoji
 *
 * @param {string} locale - Locale code (e.g., 'en', 'en-US', 'zh-TW')
 * @param {string} fallback - Fallback emoji if locale is unknown
 * @returns {string} Flag emoji or fallback
 *
 * @example
 * localeToFlag('en') // '🇺🇸'
 * localeToFlag('zh-TW') // '🇹🇼'
 * localeToFlag('ja') // '🇯🇵'
 */
export function localeToFlag(locale, fallback = '🌐') {
  if (!locale) return fallback

  // Try direct mapping
  const mappedRegion = LOCALE_TO_REGION[locale]
  if (mappedRegion) {
    return regionToFlag(mappedRegion, fallback)
  }

  // Try extracting region from locale (e.g., 'en-US' -> 'US')
  const parts = locale.split('-')
  if (parts.length > 1) {
    const regionPart = parts[parts.length - 1]
    if (regionPart.length === 2) {
      return regionToFlag(regionPart, fallback)
    }
  }

  // Use language code as fallback hint
  const langRegion = LOCALE_TO_REGION[parts[0]]
  if (langRegion) {
    return regionToFlag(langRegion, fallback)
  }

  return fallback
}

/**
 * Convert a 2-letter region code to a circle-flag SVG URL.
 * Flags are served from /flags/{code}.svg (copied from circle-flags).
 * Works on all platforms including Windows (no emoji rendering issues).
 */
export function regionToFlagUrl(region) {
  if (!region || typeof region !== 'string' || region.length !== 2) return null
  return `/flags/${region.toLowerCase()}.svg`
}

/**
 * Convert locale code to flag SVG URL.
 */
export function localeToFlagUrl(locale) {
  if (!locale) return null
  const mapped = LOCALE_TO_REGION[locale]
  if (mapped) return regionToFlagUrl(mapped)
  const parts = locale.split('-')
  if (parts.length > 1) {
    const r = parts[parts.length - 1]
    if (r.length === 2) return regionToFlagUrl(r)
  }
  const lang = LOCALE_TO_REGION[parts[0]]
  if (lang) return regionToFlagUrl(lang)
  return null
}
