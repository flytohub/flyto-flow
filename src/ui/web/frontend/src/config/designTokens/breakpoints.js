/**
 * Design Tokens - Responsive Breakpoints
 * Screen size breakpoints for responsive design
 */

export const BREAKPOINTS = Object.freeze({
  // Breakpoint values (min-width in pixels)
  XS: 0,
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536,

  // Named breakpoints for common use cases
  MOBILE: 480,
  TABLET: 768,
  DESKTOP: 1024,
  WIDE: 1400,
})

/**
 * Generate media query string
 * @param {string|number} breakpoint - Breakpoint key or pixel value
 * @param {string} type - 'min' or 'max'
 * @returns {string} Media query string
 */
export function mediaQuery(breakpoint, type = 'min') {
  const value = typeof breakpoint === 'string'
    ? BREAKPOINTS[breakpoint] || parseInt(breakpoint, 10)
    : breakpoint

  const width = type === 'max' ? value - 1 : value
  return `@media (${type}-width: ${width}px)`
}

/**
 * Check if viewport matches breakpoint
 * @param {string|number} breakpoint - Breakpoint key or pixel value
 * @param {string} type - 'min' or 'max'
 * @returns {boolean} Whether viewport matches
 */
export function matchesBreakpoint(breakpoint, type = 'min') {
  if (typeof window === 'undefined') return false

  const value = typeof breakpoint === 'string'
    ? BREAKPOINTS[breakpoint] || 0
    : breakpoint

  const width = type === 'max' ? value - 1 : value
  return window.matchMedia(`(${type}-width: ${width}px)`).matches
}
