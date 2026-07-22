import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({ get: vi.fn(), post: vi.fn() }))

import { get, post } from '@/api/client'
import { callMcpTool, getMcpStatus } from '@/api/mcp'

describe('MCP Studio API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('loads the runtime status', async () => {
    get.mockResolvedValue({ ok: true, exposedToolCount: 2, tools: [] })

    await expect(getMcpStatus()).resolves.toMatchObject({ ok: true, exposedToolCount: 2 })
    expect(get).toHaveBeenCalledWith('/mcp/status')
  })

  it('returns a stable error when the runtime is unavailable', async () => {
    get.mockRejectedValue(new Error('ECONNREFUSED'))

    await expect(getMcpStatus()).resolves.toMatchObject({
      ok: false,
      tools: [],
      error: expect.stringContaining('Start the API'),
    })
  })

  it('calls a workflow tool with the Streamable HTTP accept header', async () => {
    post.mockResolvedValue({ jsonrpc: '2.0', id: 'one', result: { isError: false } })

    const result = await callMcpTool('review_project', { target: 'repo' })

    expect(result.ok).toBe(true)
    expect(post).toHaveBeenCalledWith(
      '/mcp',
      expect.objectContaining({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: { name: 'review_project', arguments: { target: 'repo' } },
      }),
      { headers: { Accept: 'application/json, text/event-stream' } },
    )
  })

  it('preserves a JSON-RPC tool error for inspection', async () => {
    post.mockResolvedValue({ jsonrpc: '2.0', error: { message: 'Unknown tool' } })

    await expect(callMcpTool('missing')).resolves.toMatchObject({
      ok: false,
      error: 'Unknown tool',
    })
  })
})
