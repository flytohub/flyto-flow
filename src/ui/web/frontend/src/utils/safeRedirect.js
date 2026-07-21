/**
 * Safe external redirect — validates URL domain before navigating.
 * Prevents open redirect attacks via API-returned URLs.
 */

const ALLOWED_REDIRECT_DOMAINS = [
  'checkout.stripe.com',
  'connect.stripe.com',
  'billing.stripe.com',
  'dashboard.stripe.com',
  'firebasestorage.googleapis.com',
  'storage.googleapis.com',
]

/**
 * Redirect to an external URL only if it matches an allowed domain.
 * @param {string} url - The URL to redirect to
 * @param {string[]} [extraDomains] - Additional allowed domains for this redirect
 * @throws {Error} If the URL is not allowed
 */
export function safeRedirect(url, extraDomains = []) {
  if (!url || typeof url !== 'string') {
    throw new Error('Invalid redirect URL')
  }

  let parsed
  try {
    parsed = new URL(url)
  } catch {
    throw new Error('Invalid redirect URL format')
  }

  if (parsed.protocol !== 'https:') {
    throw new Error('Redirect URL must use HTTPS')
  }

  const allowed = [...ALLOWED_REDIRECT_DOMAINS, ...extraDomains]
  const isAllowed = allowed.some(
    domain => parsed.hostname === domain || parsed.hostname.endsWith(`.${domain}`)
  )

  if (!isAllowed) {
    throw new Error(`Redirect to ${parsed.hostname} is not allowed`)
  }

  window.location.href = url
}
