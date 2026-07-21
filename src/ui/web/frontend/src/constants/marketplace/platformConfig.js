/**
 * Marketplace Platform Config
 *
 * S-Grade: Dynamic platform configuration loading.
 * Single responsibility: Platform config API operations.
 */

import { get } from '@/api/client'
import { ENDPOINTS } from '@/config/api'
import i18n from '@/i18n'

// =============================================================================
// Platform Config (Dynamic)
// =============================================================================

// Cache for platform config
let platformConfigCache = null
let platformConfigCacheTime = 0
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

/**
 * Get platform configuration from Gateway API (REQUIRED - no defaults)
 * Returns cached value if available and not expired
 * @returns {Promise<{ platformFeePercent: number, minPrice: number, maxPrice: number }>}
 * @throws {Error} If config not found or incomplete
 */
export async function getPlatformConfig() {
  const now = Date.now()

  // Return cached value if still valid
  if (platformConfigCache && (now - platformConfigCacheTime) < CACHE_TTL) {
    return platformConfigCache
  }

  try {
    const result = await get(ENDPOINTS.CONFIG.PLATFORM)

    if (!result.ok) {
      throw new Error(i18n.global.t('error.platformConfigNotFound'))
    }

    // API client converts snake_case to camelCase
    const feePercent = result.platformFeePercent
    const minPrice = result.minPrice
    const maxPrice = result.maxPrice

    if (feePercent === undefined || feePercent === null) {
      throw new Error('platformFeePercent not configured.')
    }

    platformConfigCache = {
      platformFeePercent: feePercent,
      minPrice,
      maxPrice
    }
    platformConfigCacheTime = now
    return platformConfigCache
  } catch (err) {
    throw new Error(err.message || 'Failed to load platform config')
  }
}

/**
 * Get platform fee rate (convenience function)
 * @returns {Promise<number>} Fee rate as decimal (e.g., 0.20 for 20%)
 */
export async function getPlatformFeeRate() {
  const config = await getPlatformConfig()
  return config.platformFeePercent
}

/**
 * Preview fee breakdown for live typing UX.
 *
 * **Display-only hint** — the authoritative fee calculation happens
 * server-side at purchase time (see backend `api/currency.py`).
 * The backend also exposes `/config/platform/fee-preview?price=` for
 * on-demand authoritative previews.
 *
 * @param {number} price - Price amount
 * @param {number} feeRate - Fee rate as decimal (e.g., 0.20)
 * @returns {{ platformFee: number, sellerAmount: number, feePercent: number }}
 */
export function previewFeeBreakdown(price, feeRate) {
  if (!feeRate || !price) {
    return { platformFee: 0, sellerAmount: price || 0, feePercent: 0 }
  }
  const platformFee = Math.round(price * feeRate)
  const sellerAmount = price - platformFee
  const feePercent = Math.round(feeRate * 100)
  return { platformFee, sellerAmount, feePercent }
}

/**
 * Preview net credits for per-call pricing live typing UX.
 *
 * **Display-only hint** — the authoritative calculation happens
 * server-side (see backend `api/currency.calculate_net_credits`).
 * The backend also exposes `/config/platform/net-credits?call_price=`.
 *
 * @param {number} callPrice - Credits per call
 * @param {number} feePercent - Fee percentage (0-100)
 * @returns {number} Net credits after fee
 */
export function previewNetCredits(callPrice, feePercent) {
  if (!callPrice || !feePercent) return callPrice || 0
  return callPrice - Math.floor(callPrice * feePercent / 100)
}

/**
 * Clear platform config cache (for testing/refresh)
 */
export function clearPlatformConfigCache() {
  platformConfigCache = null
  platformConfigCacheTime = 0
}
