import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  request: vi.fn(),
  getRequest: vi.fn(),
  requestUse: vi.fn(),
  responseUse: vi.fn()
}))

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      request: mocks.request,
      get: mocks.getRequest,
      defaults: {},
      interceptors: {
        request: { use: mocks.requestUse },
        response: { use: mocks.responseUse }
      }
    }))
  }
}))

import { del, get, initClient, patch, post, put } from '@/api/client'

describe('local CE API client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.request.mockResolvedValue({ data: { ok: true } })
    mocks.getRequest.mockResolvedValue({ data: { auth: { mode: 'none' } } })
  })

  it.each([
    ['get', () => get('/items'), undefined],
    ['post', () => post('/items', { name: 'one' }), { name: 'one' }],
    ['put', () => put('/items/1', { name: 'two' }), { name: 'two' }],
    ['patch', () => patch('/items/1', { name: 'three' }), { name: 'three' }],
    ['delete', () => del('/items/1'), undefined]
  ])('sends %s through the same-origin client', async (method, invoke, data) => {
    await expect(invoke()).resolves.toEqual({ ok: true })
    expect(mocks.request).toHaveBeenCalledWith(expect.objectContaining({ method, data }))
  })

  it('loads runtime configuration without an identity request', async () => {
    await initClient()
    expect(mocks.getRequest).toHaveBeenCalledWith('/runtime-config')
  })
})
