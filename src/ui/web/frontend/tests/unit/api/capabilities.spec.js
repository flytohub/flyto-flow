import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({ get: vi.fn() }))

import { get } from '@/api/client'
import { getCapabilities } from '@/api/capabilities'

describe('local capabilities API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('loads execution capabilities without an identity handshake', async () => {
    get.mockResolvedValue({ ok: true, capabilities: ['execution.evidence'] })
    const result = await getCapabilities()
    expect(get).toHaveBeenCalledWith('/capabilities')
    expect(result.capabilities).toEqual(['execution.evidence'])
  })

  it('returns a stable local error envelope', async () => {
    const error = new Error('Backend unavailable')
    error.userMessage = 'Start Flyto2 Flow'
    get.mockRejectedValue(error)
    await expect(getCapabilities()).resolves.toEqual({
      ok: false,
      capabilities: [],
      error: 'Start Flyto2 Flow'
    })
  })
})
