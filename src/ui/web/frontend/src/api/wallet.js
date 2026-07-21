/**
 * Wallet / Credits API
 * Credit wallet operations: balance, transactions, topup
 */

import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import { safeRedirect } from '@/utils/safeRedirect'

/**
 * Get current credit balance
 * @returns {Promise<{ok: boolean, balance: number, balanceDollars: number}>}
 */
export async function getWalletBalance() {
  try {
    return await get(ENDPOINTS.WALLET.BALANCE)
  } catch (err) {
    return { ok: false, error: err.message, balance: 0, balanceDollars: 0 }
  }
}

/**
 * Get credit transaction history
 * @param {number} page - Page number
 * @param {number} pageSize - Items per page
 * @returns {Promise<{ok: boolean, transactions: Array, total: number, page: number, hasNext: boolean}>}
 */
export async function getWalletTransactions(page = 1, pageSize = 20) {
  try {
    return await get(ENDPOINTS.WALLET.TRANSACTIONS, {
      params: { page, pageSize }
    })
  } catch (err) {
    return { ok: false, error: err.message, transactions: [], total: 0 }
  }
}

/**
 * Get available topup packages
 * @returns {Promise<{ok: boolean, packages: Array}>}
 */
export async function getTopupPackages() {
  try {
    return await get(ENDPOINTS.WALLET.PACKAGES)
  } catch (err) {
    return { ok: false, error: err.message, packages: [] }
  }
}

/**
 * Create a Stripe Checkout Session for credit topup
 * @param {number} credits - Number of credits to purchase
 * @param {string} successUrl - URL to redirect on success
 * @param {string} cancelUrl - URL to redirect on cancel
 * @returns {Promise<{ok: boolean, sessionId: string, sessionUrl: string}>}
 */
export async function createTopupSession(credits, successUrl, cancelUrl) {
  try {
    return await post(ENDPOINTS.WALLET.TOPUP, {
      credits,
      successUrl,
      cancelUrl
    })
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Redirect to Stripe Checkout for credit topup
 * @param {number} credits - Number of credits to purchase
 */
export async function redirectToTopup(credits) {
  const baseUrl = window.location.origin

  const result = await createTopupSession(
    credits,
    `${baseUrl}/wallet?topup=success`,
    `${baseUrl}/wallet?topup=cancel`
  )

  if (result.ok && result.sessionUrl) {
    safeRedirect(result.sessionUrl)
  } else {
    throw new Error(result.error || 'Failed to create topup session')
  }
}

export default {
  getWalletBalance,
  getWalletTransactions,
  getTopupPackages,
  createTopupSession,
  redirectToTopup
}
