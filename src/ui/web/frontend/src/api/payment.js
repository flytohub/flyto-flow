/**
 * Payment API - Uses Gateway API
 * Stripe payment integration via Gateway endpoints
 */

import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import i18n from '@/i18n'
import { safeRedirect } from '@/utils/safeRedirect'

// ============== Checkout (Buyer Purchase) ==============

/**
 * Create a Stripe checkout session via Gateway API
 * @param {string} templateId - Template ID to purchase
 * @param {string} successUrl - URL to redirect on success
 * @param {string} cancelUrl - URL to redirect on cancel
 * @returns {Promise<{ok: boolean, sessionId: string, sessionUrl: string}>}
 */
export async function createCheckoutSession(templateId, successUrl, cancelUrl) {
  try {
    const result = await post(ENDPOINTS.PAYMENT.CHECKOUT, {
      templateId,
      successUrl,
      cancelUrl
    })
    return result
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Redirect to Stripe Checkout
 * @param {string} templateId - Template ID to purchase
 * @returns {Promise<void>}
 */
export async function redirectToCheckout(templateId) {
  const baseUrl = window.location.origin

  const result = await createCheckoutSession(
    templateId,
    `${baseUrl}/payment/success?template_id=${templateId}`,
    `${baseUrl}/payment/cancel?template_id=${templateId}`
  )

  // Backend /payment/checkout returns session_url -> camelCased to sessionUrl by the response interceptor
  if (result.ok && result.sessionUrl) {
    safeRedirect(result.sessionUrl)
  } else {
    throw new Error(result.error || i18n.global.t('error.failedToCreateCheckout'))
  }
}

// ============== Stripe Connect (Creator Payouts) ==============

/**
 * Get Stripe Connect account status
 * @returns {Promise<{ok: boolean, hasAccount: boolean, accountId: string, chargesEnabled: boolean, payoutsEnabled: boolean}>}
 */
export async function getConnectStatus() {
  try {
    const result = await get(ENDPOINTS.PAYMENT.CONNECT_STATUS)
    return result
  } catch (err) {
    return { ok: false, error: err.message, hasAccount: false }
  }
}

/**
 * Get Stripe Connect balance
 * @returns {Promise<{ok: boolean, available: number, pending: number, currency: string}>}
 */
export async function getConnectBalance() {
  try {
    const result = await get(ENDPOINTS.PAYMENT.CONNECT_BALANCE)
    return result
  } catch (err) {
    return { ok: false, error: err.message, available: 0, pending: 0 }
  }
}

/**
 * Get earnings summary
 * @returns {Promise<{ok: boolean, totalEarnings: number, totalSales: number, thisMonth: number}>}
 */
export async function getEarningsSummary() {
  try {
    const result = await get(ENDPOINTS.PAYMENT.EARNINGS)
    return result
  } catch (err) {
    return { ok: false, error: err.message, totalEarnings: 0, totalSales: 0, thisMonth: 0 }
  }
}

/**
 * Get recent sales
 * @param {number} limit - Number of sales to fetch
 * @returns {Promise<{ok: boolean, sales: Array}>}
 */
export async function getRecentSales(limit = 10) {
  try {
    const result = await get(ENDPOINTS.PAYMENT.SALES, {
      params: { limit }
    })
    return result
  } catch (err) {
    return { ok: false, error: err.message, sales: [] }
  }
}

/**
 * Get Connect payouts history
 * @param {number} limit - Number of payouts to fetch
 * @returns {Promise<{ok: boolean, payouts: Array}>}
 */
export async function getConnectPayouts(limit = 10) {
  try {
    const result = await get(ENDPOINTS.PAYMENT.PAYOUTS, {
      params: { limit }
    })
    return result
  } catch (err) {
    return { ok: false, error: err.message, payouts: [] }
  }
}

/**
 * Request manual payout (withdrawal)
 * @param {number|null} amount - Amount in dollars, or null for full balance
 * @param {string|null} currency - Optional payout currency
 * @returns {Promise<{ok: boolean, payout: object, message: string}>}
 */
export async function requestPayout(amount = null, currency = null) {
  try {
    const result = await post(ENDPOINTS.PAYMENT.PAYOUT_REQUEST, { amount, currency })
    return result
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Redirect to Stripe Connect onboarding
 * @param {string} country - Country code (e.g., 'US', 'TW')
 * @returns {Promise<void>}
 */
export async function redirectToConnectOnboarding(country = 'US') {
  const baseUrl = window.location.origin

  try {
    const result = await post(ENDPOINTS.PAYMENT.CONNECT_ONBOARD, {
      country,
      return_url: `${baseUrl}/settings/payout`,
      refresh_url: `${baseUrl}/settings/payout`
    })

    if (result.ok && result.url) {
      safeRedirect(result.url)
    } else {
      throw new Error(result.error || 'Failed to create Connect account')
    }
  } catch (err) {
    throw new Error(err.message || 'Failed to create Connect account')
  }
}

// ============== Purchase History (Buyer) ==============

/**
 * Get purchase history
 * @param {number} page - Page number
 * @param {number} pageSize - Items per page
 * @param {string} status - Filter by status (completed, refunded, etc.)
 * @returns {Promise<{ok: boolean, purchases: Array, total: number}>}
 */
export async function getPurchaseHistory(page = 1, pageSize = 20, status = null) {
  try {
    const params = { page, pageSize }
    if (status) params.status = status
    const result = await get(ENDPOINTS.PAYMENT.PURCHASES, { params })
    return result
  } catch (err) {
    return { ok: false, error: err.message, purchases: [], total: 0 }
  }
}

/**
 * Check refund eligibility for a purchase
 * @param {string} purchaseId - Purchase ID
 * @returns {Promise<{ok: boolean, eligible: boolean, daysRemaining: number, forksAffected: Array, warning: string}>}
 */
export async function checkRefundEligibility(purchaseId) {
  try {
    const result = await get(ENDPOINTS.PAYMENT.REFUND_ELIGIBILITY(purchaseId))
    return result
  } catch (err) {
    return { ok: false, error: err.message, eligible: false }
  }
}

/**
 * Request (and process) a refund for a purchase.
 * Issues a real Stripe refund and revokes library access on full refund.
 * @param {string} purchaseId - Purchase ID
 * @param {string} reason - Optional Stripe refund reason (requested_by_customer | duplicate | fraudulent)
 * @returns {Promise<{ok: boolean, status: string, purchase_id: string, error?: string}>}
 */
export async function requestRefund(purchaseId, reason = 'requested_by_customer') {
  try {
    const result = await post(ENDPOINTS.PAYMENT.REFUND(purchaseId), { reason })
    return result
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

export default {
  createCheckoutSession,
  redirectToCheckout,
  getConnectStatus,
  getConnectBalance,
  getEarningsSummary,
  getRecentSales,
  getConnectPayouts,
  requestPayout,
  redirectToConnectOnboarding,
  // Purchase history
  getPurchaseHistory,
  checkRefundEligibility,
  requestRefund
}
