/**
 * Design Tokens - Typography
 * Font sizes, weights, line heights
 */

export const TYPOGRAPHY = Object.freeze({
  // Font families
  FAMILY: {
    SANS: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    MONO: 'JetBrains Mono, Menlo, Monaco, Consolas, monospace',
  },

  // Font sizes (pixels)
  SIZE: {
    XS: 10,
    SM: 11,
    MD: 12,
    BASE: 13,
    LG: 14,
    XL: 16,
    '2XL': 18,
    '3XL': 20,
    '4XL': 24,
    '5XL': 30,
  },

  // Font weights
  WEIGHT: {
    NORMAL: 400,
    MEDIUM: 500,
    SEMIBOLD: 600,
    BOLD: 700,
  },

  // Line heights
  LINE_HEIGHT: {
    TIGHT: 1.25,
    NORMAL: 1.5,
    RELAXED: 1.625,
    LOOSE: 2,
  },

  // Letter spacing
  LETTER_SPACING: {
    TIGHT: '-0.025em',
    NORMAL: '0',
    WIDE: '0.025em',
    WIDER: '0.05em',
  },
})

/**
 * Get font size in rem
 * @param {string} size - Size key from TYPOGRAPHY.SIZE
 * @returns {string} Font size in rem
 */
export function getFontSize(size) {
  const px = TYPOGRAPHY.SIZE[size] || TYPOGRAPHY.SIZE.BASE
  return `${px / 16}rem`
}
