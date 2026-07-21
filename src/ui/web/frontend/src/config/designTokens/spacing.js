/**
 * Design Tokens - Spacing System
 * All spacing values in pixels, use toRem() for CSS
 * Base unit: 4px grid system
 */

export const SPACING = Object.freeze({
  // Base unit
  BASE: 4,

  // Component gaps
  COMPONENT: {
    GAP_XS: 4,
    GAP_SM: 6,
    GAP_MD: 8,
    GAP_LG: 12,
    GAP_XL: 16,
    GAP_2XL: 20,
    GAP_3XL: 24,
  },

  // Panel padding
  PANEL: {
    XS: 8,
    SM: 12,
    MD: 16,
    LG: 20,
    XL: 24,
  },

  // Form field spacing
  FIELD: {
    LABEL_GAP: 6,
    INPUT_PADDING_X: 12,
    INPUT_PADDING_Y: 10,
    HELP_GAP: 4,
    GROUP_GAP: 16,
  },

  // Section spacing
  SECTION: {
    GAP: 24,
    PADDING: 20,
  },
})

/**
 * Convert pixels to rem
 * @param {number} px - Pixel value
 * @returns {string} Rem value with unit
 */
export function toRem(px) {
  return `${px / 16}rem`
}

/**
 * Convert pixels to em
 * @param {number} px - Pixel value
 * @param {number} base - Base font size (default 16)
 * @returns {string} Em value with unit
 */
export function toEm(px, base = 16) {
  return `${px / base}em`
}
