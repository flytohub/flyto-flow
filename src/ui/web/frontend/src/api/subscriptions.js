/**
 * Subscriptions API - User Subscription Management
 * Provides API layer for Subscription.vue and AdminSubscriptions.vue
 */

import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/config/api'
import { DEFAULTS } from '@/config/defaults'

// ============== User Endpoints ==============

/**
 * Get current user's subscription
 * @returns {Promise<{ok: boolean, subscription: Object}>}
 */
export async function getMySubscription() {
  try {
    const result = await get(ENDPOINTS.SUBSCRIPTIONS.ME)
    return {
      ok: true,
      subscription: result.subscription || result
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Start a paid subscription via Stripe Checkout.
 *
 * Creates a Stripe Checkout Session on the backend (POST /subscriptions/subscribe)
 * and returns its hosted-checkout URL. The entitlement is NOT granted here — it is
 * granted only by the Stripe webhook after the payment succeeds. Callers should
 * redirect the browser to `checkoutUrl`.
 *
 * @param {Object} data - Subscription data
 * @param {string} data.planId - Plan ID (pro, team)
 * @param {string} [data.billingCycle] - Billing cycle (monthly, yearly)
 * @param {string} [data.successUrl] - Override Stripe success redirect URL
 * @param {string} [data.cancelUrl] - Override Stripe cancel redirect URL
 * @returns {Promise<{ok: boolean, checkoutUrl?: string, sessionId?: string, error?: string}>}
 */
export async function subscribe(data) {
  try {
    const result = await post(ENDPOINTS.SUBSCRIPTIONS.SUBSCRIBE, {
      plan_id: data.planId,
      billing_cycle: data.billingCycle || 'monthly',
      success_url: data.successUrl,
      cancel_url: data.cancelUrl
    })
    return {
      ok: true,
      checkoutUrl: result.session_url,
      sessionId: result.session_id
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Create a subscription record directly (ADMIN/system only — no payment).
 *
 * SECURITY: This hits POST /subscriptions/, which is admin-protected on the
 * backend and grants an entitlement without taking payment. Normal users must
 * NOT call this to upgrade — use {@link subscribe} for the paid Stripe flow.
 *
 * @param {Object} data - Subscription data
 * @returns {Promise<{ok: boolean, subscription: Object}>}
 */
export async function create(data) {
  try {
    const result = await post(ENDPOINTS.SUBSCRIPTIONS.CREATE, data)
    return {
      ok: true,
      subscription: result.subscription
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Cancel current subscription
 * @param {Object} data - Cancellation data
 * @param {string} [data.reason] - Cancellation reason
 * @param {boolean} [data.immediate] - Cancel immediately (vs end of period)
 * @returns {Promise<{ok: boolean}>}
 */
export async function cancel(data = {}) {
  try {
    await post(ENDPOINTS.SUBSCRIPTIONS.CANCEL, data)
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

// ============== Admin Endpoints ==============

/**
 * List all subscriptions (admin only)
 * @param {Object} [params] - Query parameters
 * @param {string} [params.status] - Filter by status (active, cancelled, expired)
 * @param {string} [params.planId] - Filter by plan
 * @param {number} [params.page] - Page number
 * @param {number} [params.pageSize] - Page size
 * @returns {Promise<{ok: boolean, subscriptions: Array, total: number}>}
 */
export async function list({ status = null, planId = null, page = 1, pageSize = DEFAULTS.PAGINATION.ADMIN } = {}) {
  try {
    const result = await get(ENDPOINTS.SUBSCRIPTIONS.LIST, {
      params: { status, planId, page, pageSize }
    })
    return {
      ok: true,
      subscriptions: result.subscriptions || [],
      total: result.total || 0,
      page: result.page || page,
      pageSize: result.pageSize || pageSize
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message, subscriptions: [], total: 0 }
  }
}

/**
 * Get subscription by ID (admin only)
 * @param {string} id - Subscription ID
 * @returns {Promise<{ok: boolean, subscription: Object}>}
 */
export async function getById(id) {
  try {
    const result = await get(ENDPOINTS.SUBSCRIPTIONS.GET(id))
    return { ok: true, subscription: result.subscription || result }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Grant subscription to a user (admin only)
 * @param {Object} data - Grant data
 * @param {string} data.userId - User ID
 * @param {string} data.planId - Plan ID
 * @param {number} data.durationDays - Duration in days
 * @param {string} [data.reason] - Grant reason
 * @returns {Promise<{ok: boolean, subscription: Object}>}
 */
export async function grant(data) {
  try {
    const result = await post(ENDPOINTS.SUBSCRIPTIONS.GRANT, data)
    return { ok: true, subscription: result.subscription || result }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}

/**
 * Get subscription statistics (admin only)
 * @returns {Promise<{ok: boolean, stats: Object}>}
 */
export async function getStats() {
  try {
    const result = await get(ENDPOINTS.SUBSCRIPTIONS.STATS)
    return {
      ok: true,
      stats: result.stats || result
    }
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message, stats: {} }
  }
}

export const subscriptionsAPI = {
  // User
  getMySubscription,
  subscribe,
  create,
  cancel,
  // Admin
  list,
  get: getById,
  grant,
  getStats
}

export default subscriptionsAPI
