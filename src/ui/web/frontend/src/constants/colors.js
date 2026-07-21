/**
 * Category Color Constants
 *
 * NOTE: These are FALLBACK colors only.
 * Primary source of truth is flyto-core via API (modulesStore.modulesMetadata)
 */

// Default fallback color when category not found
export const DEFAULT_COLOR = '#6C757D'
export const DEFAULT_GRADIENT = 'linear-gradient(135deg, #6C757D 0%, #868E96 100%)'

// Minimal fallback map (only for edge cases when API data not available)
export const CATEGORY_COLORS = {
  default: { color: DEFAULT_COLOR, gradient: DEFAULT_GRADIENT }
}

/**
 * Get category color (fallback only)
 * @param {string} category - Category slug
 * @returns {string} Hex color
 */
export function getCategoryColor(category) {
  return (CATEGORY_COLORS[category] || CATEGORY_COLORS.default).color
}

/**
 * Get category gradient (fallback only)
 * @param {string} category - Category slug
 * @returns {string} CSS gradient
 */
export function getCategoryGradient(category) {
  return (CATEGORY_COLORS[category] || CATEGORY_COLORS.default).gradient
}

/**
 * Get both color and gradient for a category (fallback only)
 * @param {string} category - Category slug
 * @returns {{ color: string, gradient: string }}
 */
export function getCategoryColors(category) {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.default
}

export default {
  CATEGORY_COLORS,
  DEFAULT_COLOR,
  DEFAULT_GRADIENT,
  getCategoryColor,
  getCategoryGradient,
  getCategoryColors
}
