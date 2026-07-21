import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
}))

import { get } from '@/api/client'
import { getMcpStatus } from '@/api/mcp'

describe('MCP API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads MCP status from backend endpoint', async () => {
    get.mockResolvedValue({ ok: true, exposedToolCount: 1, tools: [{ name: 'smoke' }] })

    const result = await getMcpStatus()

    expect(get).toHaveBeenCalledWith('/mcp/status')
    expect(result.exposedToolCount).toBe(1)
  })

  it('normalizes MCP backend outage errors', async () => {
    get.mockRejectedValue(new Error('Network Error'))

    const result = await getMcpStatus()

    expect(result).toEqual({
      ok: false,
      tools: [],
      exposedToolCount: 0,
      error: 'MCP status unavailable. Start the cloud API or try again after the backend is healthy.',
    })
  })
})
