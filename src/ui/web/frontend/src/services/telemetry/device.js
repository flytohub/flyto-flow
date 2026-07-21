/**
 * Device & Performance Detection
 *
 * Browser/OS detection, device fingerprinting, and performance metrics.
 */

// Cache device info (doesn't change during session)
let cachedDeviceInfo = null

/**
 * Get device and browser information
 * @returns {Object} Device info
 */
export function getDeviceInfo() {
  if (cachedDeviceInfo) return cachedDeviceInfo

  const ua = navigator.userAgent
  let browser = 'unknown'
  let os = 'unknown'

  // Detect browser
  if (ua.includes('Firefox')) browser = 'Firefox'
  else if (ua.includes('Edg')) browser = 'Edge'
  else if (ua.includes('Chrome')) browser = 'Chrome'
  else if (ua.includes('Safari')) browser = 'Safari'

  // Detect OS
  if (ua.includes('Windows')) os = 'Windows'
  else if (ua.includes('Mac')) os = 'macOS'
  else if (ua.includes('Linux')) os = 'Linux'
  else if (ua.includes('Android')) os = 'Android'
  else if (ua.includes('iPhone') || ua.includes('iPad')) os = 'iOS'

  cachedDeviceInfo = {
    screen_width: window.screen?.width,
    screen_height: window.screen?.height,
    viewport_width: window.innerWidth,
    viewport_height: window.innerHeight,
    device_pixel_ratio: window.devicePixelRatio,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    browser,
    os,
    is_mobile: /Android|iPhone|iPad|iPod|Opera Mini|IEMobile/i.test(ua),
    is_touch: 'ontouchstart' in window || navigator.maxTouchPoints > 0
  }

  return cachedDeviceInfo
}

/**
 * Get performance metrics (for page.view events)
 * @returns {Object|null} Performance metrics
 */
export function getPerformanceMetrics() {
  try {
    const nav = performance.getEntriesByType('navigation')[0]
    if (!nav) return null

    return {
      dns_ms: Math.round(nav.domainLookupEnd - nav.domainLookupStart),
      connect_ms: Math.round(nav.connectEnd - nav.connectStart),
      ttfb_ms: Math.round(nav.responseStart - nav.requestStart),
      dom_load_ms: Math.round(nav.domContentLoadedEventEnd - nav.startTime),
      page_load_ms: Math.round(nav.loadEventEnd - nav.startTime),
      transfer_size: nav.transferSize
    }
  } catch {
    return null
  }
}
