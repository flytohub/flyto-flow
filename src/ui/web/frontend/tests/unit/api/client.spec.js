import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock dependencies before importing client
vi.mock('axios', () => {
  const interceptors = {
    request: { use: vi.fn() },
    response: { use: vi.fn() }
  }
  const instance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors
  }
  return {
    default: {
      create: vi.fn(() => instance),
      __instance: instance
    }
  }
})

vi.mock('@/config/api', () => ({
  API_URL: '/api',
  REQUEST_TIMEOUT: 30000,
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'access_token',
    REFRESH_TOKEN: 'refresh_token',
    USER: 'user'
  },
  ENDPOINTS: {
    AUTH: {
      REFRESH: '/auth/refresh',
      ME: '/auth/me',
      LOGIN: '/auth/login',
      GOOGLE_LOGIN: '/auth/google-login',
      GITHUB_LOGIN: '/auth/github-login'
    }
  }
}))

vi.mock('@/utils/payloadEncryption', () => ({
  isEncryptionEnabled: vi.fn(() => Promise.resolve(false)),
  generateRequestKey: vi.fn(),
  encryptPayload: vi.fn(),
  decryptResponse: vi.fn()
}))

vi.mock('@/services/telemetry', () => ({
  telemetry: {
    getTraceId: vi.fn(() => 'trace-123'),
    getSessionId: vi.fn(() => 'session-456'),
    track: vi.fn(),
    trackApiError: vi.fn()
  }
}))

vi.mock('@/utils/telemetryTracker', () => ({
  trackUX: {
    permissionDenied: vi.fn(),
    quotaExceeded: vi.fn(),
    timeout: vi.fn(),
    apiError: vi.fn()
  },
  trackPerformance: {
    slowApi: vi.fn()
  }
}))

import axios from 'axios'
import { get, post, put, patch, del, upload, download, initClient, axiosInstance } from '@/api/client'

describe('API Client', () => {
  let mockInstance

  beforeEach(() => {
    vi.clearAllMocks()
    mockInstance = axios.__instance
    localStorage.clear()
  })

  // =========================================================================
  // Axios Instance Creation
  // =========================================================================

  describe('axios instance creation', () => {
    it('exports a working axios instance', () => {
      // axios.create was called at module load time (before clearAllMocks),
      // so we verify the exported instance is the mock instance
      expect(axiosInstance).toBeDefined()
      expect(typeof axiosInstance.get).toBe('function')
      expect(typeof axiosInstance.post).toBe('function')
    })

    it('has interceptors registered', () => {
      // Interceptors are set up at module load time
      expect(axiosInstance.interceptors).toBeDefined()
      expect(axiosInstance.interceptors.request).toBeDefined()
      expect(axiosInstance.interceptors.response).toBeDefined()
    })
  })

  // =========================================================================
  // GET requests
  // =========================================================================

  describe('get()', () => {
    it('calls axios.get and returns response.data', async () => {
      const responseData = { ok: true, items: [1, 2, 3] }
      mockInstance.get.mockResolvedValue({ data: responseData })

      const result = await get('/test-endpoint')

      expect(mockInstance.get).toHaveBeenCalledWith('/test-endpoint', {})
      expect(result).toEqual(responseData)
    })

    it('passes additional config to axios', async () => {
      mockInstance.get.mockResolvedValue({ data: { ok: true } })

      await get('/test', { params: { page: 1 }, headers: { 'X-Custom': 'val' } })

      expect(mockInstance.get).toHaveBeenCalledWith('/test', {
        params: { page: 1 },
        headers: { 'X-Custom': 'val' }
      })
    })

    it('strips retry config before passing to axios', async () => {
      mockInstance.get.mockResolvedValue({ data: { ok: true } })

      await get('/test', { retry: { maxRetries: 5 }, params: { q: 'search' } })

      expect(mockInstance.get).toHaveBeenCalledWith('/test', { params: { q: 'search' } })
    })

    it('propagates errors from axios', async () => {
      const error = new Error('Bad Request')
      error.response = { status: 400 }
      mockInstance.get.mockRejectedValue(error)

      await expect(get('/fail')).rejects.toThrow('Bad Request')
    }, 10000)
  })

  // =========================================================================
  // POST requests
  // =========================================================================

  describe('post()', () => {
    it('calls axios.post with url and data, returns response.data', async () => {
      const responseData = { ok: true, id: 'abc' }
      mockInstance.post.mockResolvedValue({ data: responseData })

      const result = await post('/items', { name: 'test' })

      expect(mockInstance.post).toHaveBeenCalledWith('/items', { name: 'test' }, {})
      expect(result).toEqual(responseData)
    })

    it('sends empty object by default when no data provided', async () => {
      mockInstance.post.mockResolvedValue({ data: { ok: true } })

      await post('/items')

      expect(mockInstance.post).toHaveBeenCalledWith('/items', {}, {})
    })

    it('passes additional config to axios', async () => {
      mockInstance.post.mockResolvedValue({ data: { ok: true } })

      await post('/items', { a: 1 }, { headers: { 'X-Key': 'val' } })

      expect(mockInstance.post).toHaveBeenCalledWith('/items', { a: 1 }, { headers: { 'X-Key': 'val' } })
    })
  })

  // =========================================================================
  // PUT requests
  // =========================================================================

  describe('put()', () => {
    it('calls axios.put with url and data, returns response.data', async () => {
      mockInstance.put.mockResolvedValue({ data: { ok: true } })

      const result = await put('/items/1', { name: 'updated' })

      expect(mockInstance.put).toHaveBeenCalledWith('/items/1', { name: 'updated' }, {})
      expect(result).toEqual({ ok: true })
    })
  })

  // =========================================================================
  // PATCH requests
  // =========================================================================

  describe('patch()', () => {
    it('calls axios.patch with url and data, returns response.data', async () => {
      mockInstance.patch.mockResolvedValue({ data: { ok: true } })

      const result = await patch('/items/1', { status: 'active' })

      expect(mockInstance.patch).toHaveBeenCalledWith('/items/1', { status: 'active' }, {})
      expect(result).toEqual({ ok: true })
    })
  })

  // =========================================================================
  // DELETE requests
  // =========================================================================

  describe('del()', () => {
    it('calls axios.delete with url and returns response.data', async () => {
      mockInstance.delete.mockResolvedValue({ data: { ok: true } })

      const result = await del('/items/1')

      expect(mockInstance.delete).toHaveBeenCalledWith('/items/1', {})
      expect(result).toEqual({ ok: true })
    })
  })

  // =========================================================================
  // Upload
  // =========================================================================

  describe('upload()', () => {
    it('posts FormData with progress callback', async () => {
      const formData = new FormData()
      const onProgress = vi.fn()
      mockInstance.post.mockResolvedValue({ data: { ok: true, url: '/file.png' } })

      const result = await upload('/storage/upload', formData, onProgress)

      expect(mockInstance.post).toHaveBeenCalledWith('/storage/upload', formData, {
        onUploadProgress: onProgress
      })
      expect(result).toEqual({ ok: true, url: '/file.png' })
    })
  })

  // =========================================================================
  // initClient
  // =========================================================================

  describe('initClient()', () => {
    it('is a no-op that resolves', async () => {
      await expect(initClient()).resolves.toBeUndefined()
    })
  })

  // =========================================================================
  // Retry logic (via exported get/post)
  // =========================================================================

  describe('retry logic', () => {
    it('retries on retryable status codes', async () => {
      const error502 = new Error('Bad Gateway')
      error502.response = { status: 502 }

      mockInstance.get
        .mockRejectedValueOnce(error502)
        .mockResolvedValueOnce({ data: { ok: true } })

      const result = await get('/retry-test', { retry: { maxRetries: 2, baseDelay: 1 } })

      expect(mockInstance.get).toHaveBeenCalledTimes(2)
      expect(result).toEqual({ ok: true })
    })

    it('does not retry on non-retryable status codes (e.g., 400)', async () => {
      const error400 = new Error('Bad Request')
      error400.response = { status: 400 }

      mockInstance.get.mockRejectedValue(error400)

      await expect(get('/no-retry', { retry: { maxRetries: 3 } })).rejects.toThrow('Bad Request')
      expect(mockInstance.get).toHaveBeenCalledTimes(1)
    })

    it('retries on network errors', async () => {
      const networkError = new Error('Network Error')
      networkError.code = 'ERR_NETWORK'

      mockInstance.post
        .mockRejectedValueOnce(networkError)
        .mockResolvedValueOnce({ data: { ok: true } })

      const result = await post('/network-retry', {}, { retry: { maxRetries: 1, baseDelay: 1 } })

      expect(mockInstance.post).toHaveBeenCalledTimes(2)
      expect(result).toEqual({ ok: true })
    })

    it('retries on timeout errors', async () => {
      const timeoutError = new Error('timeout of 30000ms exceeded')
      timeoutError.code = 'ECONNABORTED'

      mockInstance.get
        .mockRejectedValueOnce(timeoutError)
        .mockResolvedValueOnce({ data: { ok: true } })

      const result = await get('/timeout-retry', { retry: { maxRetries: 1, baseDelay: 1 } })

      expect(mockInstance.get).toHaveBeenCalledTimes(2)
      expect(result).toEqual({ ok: true })
    })

    it('throws after exhausting all retry attempts', async () => {
      const error503 = new Error('Service Unavailable')
      error503.response = { status: 503 }

      mockInstance.get.mockRejectedValue(error503)

      await expect(
        get('/exhaust-retry', { retry: { maxRetries: 2, baseDelay: 1, maxDelay: 2 } })
      ).rejects.toThrow('Service Unavailable')

      // 1 initial + 2 retries = 3 total
      expect(mockInstance.get).toHaveBeenCalledTimes(3)
    })
  })

  // =========================================================================
  // axiosInstance export
  // =========================================================================

  describe('axiosInstance export', () => {
    it('exports the underlying axios instance', () => {
      expect(axiosInstance).toBe(mockInstance)
    })
  })
})
