import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

vi.mock('@/api/config', () => ({
  ENDPOINTS: {
    PAYMENT: {
      CHECKOUT: '/payment/checkout',
      CONNECT_STATUS: '/payment/connect/status',
      CONNECT_BALANCE: '/payment/connect/balance',
      CONNECT_ONBOARD: '/payment/connect/onboard',
      EARNINGS: '/payment/earnings',
      SALES: '/payment/sales',
      PAYOUTS: '/payment/payouts',
      PAYOUT_REQUEST: '/payment/payout',
      PURCHASES: '/payment/purchases',
      REFUND_ELIGIBILITY: (id) => `/payment/purchases/${id}/refund-eligibility`
    }
  }
}))

vi.mock('@/i18n', () => ({
  default: {
    global: {
      t: vi.fn((key) => key)
    }
  }
}))

import { get, post } from '@/api/client'
import {
  createCheckoutSession,
  getConnectStatus,
  getConnectBalance,
  getEarningsSummary,
  getRecentSales,
  getConnectPayouts,
  requestPayout,
  getPurchaseHistory,
  checkRefundEligibility
} from '@/api/payment'

describe('Payment API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // createCheckoutSession
  // =========================================================================

  describe('createCheckoutSession()', () => {
    it('calls POST /payment/checkout with template and URLs', async () => {
      post.mockResolvedValue({ ok: true, url: 'https://stripe.com/checkout/sess_1' })

      const result = await createCheckoutSession(
        'tmpl-1',
        'https://app.com/success',
        'https://app.com/cancel'
      )

      expect(post).toHaveBeenCalledWith('/payment/checkout', {
        templateId: 'tmpl-1',
        successUrl: 'https://app.com/success',
        cancelUrl: 'https://app.com/cancel'
      })
      expect(result.ok).toBe(true)
      expect(result.url).toContain('stripe.com')
    })

    it('returns error object on failure', async () => {
      post.mockRejectedValue(new Error('Payment service unavailable'))

      const result = await createCheckoutSession('tmpl-1', 'url', 'url')

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Payment service unavailable')
    })
  })

  // =========================================================================
  // getConnectStatus
  // =========================================================================

  describe('getConnectStatus()', () => {
    it('calls GET /payment/connect/status', async () => {
      get.mockResolvedValue({ ok: true, hasAccount: true, chargesEnabled: true })

      const result = await getConnectStatus()

      expect(get).toHaveBeenCalledWith('/payment/connect/status')
      expect(result.hasAccount).toBe(true)
    })

    it('returns fallback on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const result = await getConnectStatus()

      expect(result.ok).toBe(false)
      expect(result.hasAccount).toBe(false)
    })
  })

  // =========================================================================
  // getConnectBalance
  // =========================================================================

  describe('getConnectBalance()', () => {
    it('calls GET /payment/connect/balance', async () => {
      get.mockResolvedValue({ ok: true, available: 5000, pending: 1000, currency: 'usd' })

      const result = await getConnectBalance()

      expect(get).toHaveBeenCalledWith('/payment/connect/balance')
      expect(result.available).toBe(5000)
    })

    it('returns zero balance on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const result = await getConnectBalance()

      expect(result.available).toBe(0)
      expect(result.pending).toBe(0)
    })
  })

  // =========================================================================
  // getEarningsSummary
  // =========================================================================

  describe('getEarningsSummary()', () => {
    it('calls GET /payment/earnings', async () => {
      get.mockResolvedValue({ ok: true, totalEarnings: 10000, totalSales: 50 })

      const result = await getEarningsSummary()

      expect(get).toHaveBeenCalledWith('/payment/earnings')
      expect(result.totalEarnings).toBe(10000)
    })

    it('returns zero values on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const result = await getEarningsSummary()

      expect(result.totalEarnings).toBe(0)
      expect(result.totalSales).toBe(0)
    })
  })

  // =========================================================================
  // getRecentSales
  // =========================================================================

  describe('getRecentSales()', () => {
    it('calls GET /payment/sales with limit param', async () => {
      get.mockResolvedValue({ ok: true, sales: [{ id: 's1' }] })

      const result = await getRecentSales(5)

      expect(get).toHaveBeenCalledWith('/payment/sales', { params: { limit: 5 } })
      expect(result.sales).toHaveLength(1)
    })

    it('defaults limit to 10', async () => {
      get.mockResolvedValue({ ok: true, sales: [] })

      await getRecentSales()

      expect(get).toHaveBeenCalledWith('/payment/sales', { params: { limit: 10 } })
    })
  })

  // =========================================================================
  // getConnectPayouts
  // =========================================================================

  describe('getConnectPayouts()', () => {
    it('calls GET /payment/payouts with limit param', async () => {
      get.mockResolvedValue({ ok: true, payouts: [] })

      await getConnectPayouts(20)

      expect(get).toHaveBeenCalledWith('/payment/payouts', { params: { limit: 20 } })
    })

    it('returns empty payouts on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const result = await getConnectPayouts()

      expect(result.payouts).toEqual([])
    })
  })

  // =========================================================================
  // requestPayout
  // =========================================================================

  describe('requestPayout()', () => {
    it('calls POST /payment/payout with amount and currency', async () => {
      post.mockResolvedValue({ ok: true, payout: { id: 'po_1' } })

      const result = await requestPayout(5000, 'usd')

      expect(post).toHaveBeenCalledWith('/payment/payout', { amount: 5000, currency: 'usd' })
      expect(result.ok).toBe(true)
    })

    it('sends null amount for full balance withdrawal', async () => {
      post.mockResolvedValue({ ok: true })

      await requestPayout()

      expect(post).toHaveBeenCalledWith('/payment/payout', { amount: null, currency: null })
    })
  })

  // =========================================================================
  // getPurchaseHistory
  // =========================================================================

  describe('getPurchaseHistory()', () => {
    it('calls GET /payment/purchases with pagination', async () => {
      get.mockResolvedValue({ ok: true, purchases: [], total: 0 })

      await getPurchaseHistory(2, 10, 'completed')

      expect(get).toHaveBeenCalledWith('/payment/purchases', {
        params: { page: 2, pageSize: 10, status: 'completed' }
      })
    })

    it('omits status when null', async () => {
      get.mockResolvedValue({ ok: true, purchases: [] })

      await getPurchaseHistory()

      const params = get.mock.calls[0][1].params
      expect(params.status).toBeUndefined()
    })
  })

  // =========================================================================
  // checkRefundEligibility
  // =========================================================================

  describe('checkRefundEligibility()', () => {
    it('calls GET /payment/purchases/:id/refund-eligibility', async () => {
      get.mockResolvedValue({ ok: true, eligible: true, daysRemaining: 5 })

      const result = await checkRefundEligibility('pur-1')

      expect(get).toHaveBeenCalledWith('/payment/purchases/pur-1/refund-eligibility')
      expect(result.eligible).toBe(true)
    })

    it('returns not eligible on error', async () => {
      get.mockRejectedValue(new Error('fail'))

      const result = await checkRefundEligibility('bad')

      expect(result.eligible).toBe(false)
    })
  })
})
