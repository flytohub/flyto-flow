import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

import { get, post } from '@/api/client'
import { getCapabilities, reloadCapabilities } from '@/api/capabilities'

describe('Capabilities API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getCapabilities()', () => {
    it('calls GET /capabilities', async () => {
      get.mockResolvedValue({
        deploymentMode: 'cloud',
        licenseType: 'subscription',
        isLicensed: true,
        capabilities: ['auth.firebase', 'marketplace'],
        features: { marketplace: true, billing: true }
      })

      const result = await getCapabilities()

      expect(get).toHaveBeenCalledWith('/capabilities')
      expect(result.deploymentMode).toBe('cloud')
      expect(result.capabilities).toContain('marketplace')
    })

    it('returns error object on failure', async () => {
      const error = new Error('Server down')
      error.userMessage = 'Service unavailable'
      get.mockRejectedValue(error)

      const result = await getCapabilities()

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Service unavailable')
    })

    it('falls back to error.message if no userMessage', async () => {
      get.mockRejectedValue(new Error('Network Error'))

      const result = await getCapabilities()

      expect(result.error).toBe('Network Error')
    })
  })

  describe('reloadCapabilities()', () => {
    it('calls POST /capabilities/reload', async () => {
      post.mockResolvedValue({
        deploymentMode: 'enterprise',
        isLicensed: true
      })

      const result = await reloadCapabilities()

      expect(post).toHaveBeenCalledWith('/capabilities/reload')
      expect(result.isLicensed).toBe(true)
    })

    it('returns error object on failure', async () => {
      post.mockRejectedValue(new Error('Forbidden'))

      const result = await reloadCapabilities()

      expect(result.ok).toBe(false)
    })
  })
})
