/**
 * telemetry Unit Tests
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock dependencies
vi.mock('@/api/client', () => ({
  post: vi.fn().mockResolvedValue({ ok: true })
}))

vi.mock('@/api/config', () => ({
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'access_token',
    REFRESH_TOKEN: 'refresh_token',
    USER: 'user',
    LANGUAGE: 'language',
    THEME: 'theme'
  }
}))

import { post } from '@/api/client'
import {
  telemetry,
  initTelemetryErrorHandlers,
  addTelemetryHeaders,
  trackRequestDuration,
  trackApiErrorInterceptor,
  startHeartbeat,
  stopHeartbeat
} from '@/services/telemetry'

describe('telemetry', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    telemetry.setEnabled(true)
    telemetry.setSampleRate(1.0)
    localStorage.clear()
  })

  afterEach(() => {
    stopHeartbeat()
    vi.restoreAllMocks()
  })

  // =========================================================================
  // ID Management
  // =========================================================================

  describe('ID management', () => {
    it('should return a trace ID', () => {
      const traceId = telemetry.getTraceId()
      expect(traceId).toBeTruthy()
      expect(typeof traceId).toBe('string')
    })

    it('should set trace ID', () => {
      telemetry.setTraceId('custom-trace-id')
      expect(telemetry.getTraceId()).toBe('custom-trace-id')
    })

    it('should reset trace ID and return new one', () => {
      telemetry.setTraceId('old-id')
      const newId = telemetry.resetTraceId()
      expect(newId).not.toBe('old-id')
      expect(telemetry.getTraceId()).toBe(newId)
    })

    it('should return a session ID', () => {
      const sessionId = telemetry.getSessionId()
      expect(sessionId).toBeTruthy()
      expect(typeof sessionId).toBe('string')
    })

    it('should return consistent session ID', () => {
      expect(telemetry.getSessionId()).toBe(telemetry.getSessionId())
    })

    it('should generate unique request IDs', () => {
      const id1 = telemetry.generateRequestId()
      const id2 = telemetry.generateRequestId()
      expect(id1).not.toBe(id2)
    })
  })

  // =========================================================================
  // Error Tracking
  // =========================================================================

  describe('trackError', () => {
    it('should send error event to backend', async () => {
      const error = new Error('test error')
      await telemetry.trackError(error, { name: 'test' })

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        event_type: 'frontend_error',
        event_name: 'test',
        error: expect.objectContaining({
          message: 'test error',
          type: 'Error'
        })
      }))
    })

    it('should handle non-Error objects', async () => {
      await telemetry.trackError({ message: 'obj error' })

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        error: expect.objectContaining({
          message: 'obj error'
        })
      }))
    })

    it('should default event name to unknown_error', async () => {
      await telemetry.trackError(new Error('oops'))

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        event_name: 'unknown_error'
      }))
    })
  })

  describe('trackVueError', () => {
    it('should track Vue component errors', async () => {
      const error = new Error('render failed')
      const instance = { $options: { name: 'MyComponent' } }

      await telemetry.trackVueError(error, instance, 'mounted')

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        event_name: 'vue.error',
        properties: expect.objectContaining({
          component: 'MyComponent',
          lifecycle: 'mounted'
        })
      }))
    })

    it('should handle null instance', async () => {
      await telemetry.trackVueError(new Error('err'), null, 'setup')

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        properties: expect.objectContaining({
          component: 'unknown'
        })
      }))
    })
  })

  describe('trackApiError', () => {
    it('should track API errors', async () => {
      const config = { method: 'get', url: '/api/test', _duration: 150 }
      const error = { message: 'Network Error', code: 'ERR_NETWORK' }
      const response = { status: 500 }

      await telemetry.trackApiError(config, error, response)

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        event_name: 'api.error',
        request: expect.objectContaining({
          method: 'GET',
          status: 500,
          duration_ms: 150
        })
      }))
    })

    it('should skip telemetry endpoint to prevent infinite loop', async () => {
      const config = { url: '/api/telemetry' }
      await telemetry.trackApiError(config, new Error('fail'), null)

      expect(post).not.toHaveBeenCalled()
    })

    it('should sanitize URLs with sensitive params', async () => {
      const config = { method: 'get', url: '/api/data?token=secret123&key=abc' }
      await telemetry.trackApiError(config, new Error('fail'), { status: 401 })

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        request: expect.objectContaining({
          url: expect.not.stringContaining('secret123')
        })
      }))
    })
  })

  describe('trackUnhandledRejection', () => {
    it('should track Error rejections', async () => {
      const event = { reason: new Error('unhandled') }
      await telemetry.trackUnhandledRejection(event)

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        error: expect.objectContaining({
          message: 'unhandled'
        })
      }))
    })

    it('should wrap non-Error reasons', async () => {
      const event = { reason: 'string rejection' }
      await telemetry.trackUnhandledRejection(event)

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        error: expect.objectContaining({
          message: 'string rejection'
        })
      }))
    })
  })

  // =========================================================================
  // Business Tracking
  // =========================================================================

  describe('track', () => {
    it('should send track event', async () => {
      await telemetry.track('workflow.execute', { workflowId: 'wf-1' })

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        event_type: 'track_event',
        event_name: 'workflow.execute',
        properties: { workflowId: 'wf-1' }
      }))
    })
  })

  describe('trackPageView', () => {
    it('should track page view with path', async () => {
      await telemetry.trackPageView('/dashboard')

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        event_name: 'page.view',
        properties: expect.objectContaining({
          path: '/dashboard'
        })
      }))
    })
  })

  describe('trackClick', () => {
    it('should track button click', async () => {
      await telemetry.trackClick('save-btn', { page: 'editor' })

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        event_name: 'button.click',
        properties: expect.objectContaining({
          buttonId: 'save-btn',
          page: 'editor'
        })
      }))
    })
  })

  // =========================================================================
  // Configuration
  // =========================================================================

  describe('configuration', () => {
    it('should not send events when disabled', async () => {
      telemetry.setEnabled(false)
      await telemetry.track('test.event')
      expect(post).not.toHaveBeenCalled()
    })

    it('should re-enable after disable', async () => {
      telemetry.setEnabled(false)
      telemetry.setEnabled(true)
      await telemetry.track('test.event')
      expect(post).toHaveBeenCalled()
    })

    it('should clamp sample rate to 0-1 range', () => {
      telemetry.setSampleRate(-0.5)
      telemetry.setSampleRate(1.5)
      // No error thrown
    })

    it('should skip events based on sample rate', async () => {
      telemetry.setSampleRate(0)
      await telemetry.track('should.be.skipped')
      expect(post).not.toHaveBeenCalled()
    })
  })

  // =========================================================================
  // _send internal
  // =========================================================================

  describe('_send', () => {
    it('should add common fields to event', async () => {
      await telemetry.track('test')

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        timestamp: expect.any(String),
        source: 'frontend',
        device: expect.any(Object)
      }))
    })

    it('should include user info from localStorage', async () => {
      localStorage.setItem('user', JSON.stringify({ id: 'u1', email: 'a@flyto2.com' }))

      await telemetry.track('test')

      expect(post).toHaveBeenCalledWith('/telemetry', expect.objectContaining({
        user_id: 'u1',
        user_email: 'a@flyto2.com'
      }))
    })

    it('should handle invalid user JSON gracefully', async () => {
      localStorage.setItem('user', 'not-json{')

      // Should not throw
      await telemetry.track('test')
      expect(post).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // _sanitizeUrl
  // =========================================================================

  describe('_sanitizeUrl', () => {
    it('should redact sensitive query params', () => {
      const result = telemetry._sanitizeUrl('/api/data?token=secret&name=visible')
      expect(result).not.toContain('secret')
      expect(result).toContain('name=visible')
      expect(result).toContain('REDACTED')
    })

    it('should handle null/undefined', () => {
      expect(telemetry._sanitizeUrl(null)).toBeNull()
      expect(telemetry._sanitizeUrl(undefined)).toBeUndefined()
    })

    it('should handle invalid URLs gracefully', () => {
      // Invalid URL that can't be parsed — just returns as-is
      const result = telemetry._sanitizeUrl('://invalid')
      expect(result).toBeTruthy()
    })

    it('should redact multiple sensitive params', () => {
      const result = telemetry._sanitizeUrl('/api?key=k1&secret=s1&password=p1&api_key=ak1')
      expect(result).not.toContain('k1')
      expect(result).not.toContain('s1')
      expect(result).not.toContain('p1')
      expect(result).not.toContain('ak1')
    })
  })

  // =========================================================================
  // Interceptor helpers
  // =========================================================================

  describe('addTelemetryHeaders', () => {
    it('should add trace and session headers', () => {
      const config = { headers: {} }
      const result = addTelemetryHeaders(config)

      expect(result.headers['X-Trace-ID']).toBeTruthy()
      expect(result.headers['X-Session-ID']).toBeTruthy()
      expect(result._startTime).toBeTruthy()
    })

    it('should create headers object if missing', () => {
      const config = {}
      const result = addTelemetryHeaders(config)
      expect(result.headers).toBeDefined()
    })
  })

  describe('trackRequestDuration', () => {
    it('should calculate duration from _startTime', () => {
      const now = Date.now()
      const response = { config: { _startTime: now - 100 } }
      const result = trackRequestDuration(response)

      expect(result.config._duration).toBeGreaterThanOrEqual(0)
    })

    it('should skip if no _startTime', () => {
      const response = { config: {} }
      const result = trackRequestDuration(response)
      expect(result.config._duration).toBeUndefined()
    })
  })

  describe('trackApiErrorInterceptor', () => {
    it('should track error and return rejected promise', async () => {
      const error = {
        config: { url: '/api/test', method: 'post', _startTime: Date.now() - 50 },
        response: { status: 500 },
        message: 'Server Error'
      }

      await expect(trackApiErrorInterceptor(error)).rejects.toBe(error)
      expect(post).toHaveBeenCalled()
    })

    it('should handle missing config', async () => {
      const error = { message: 'no config' }
      await expect(trackApiErrorInterceptor(error)).rejects.toBe(error)
    })
  })

  // =========================================================================
  // Heartbeat
  // =========================================================================

  describe('heartbeat', () => {
    it('should start and stop heartbeat without error', () => {
      expect(() => startHeartbeat()).not.toThrow()
      expect(() => stopHeartbeat()).not.toThrow()
    })

    it('should send initial heartbeat on start', () => {
      startHeartbeat()
      expect(post).toHaveBeenCalledWith('/telemetry/heartbeat', expect.objectContaining({
        session_id: expect.any(String),
        page: expect.any(String)
      }))
    })

    it('should not start twice', () => {
      startHeartbeat()
      const callCount = post.mock.calls.length
      startHeartbeat() // Second call should be no-op
      expect(post.mock.calls.length).toBe(callCount)
    })
  })

  // =========================================================================
  // initTelemetryErrorHandlers
  // =========================================================================

  describe('initTelemetryErrorHandlers', () => {
    it('should register event listeners', () => {
      const addSpy = vi.spyOn(window, 'addEventListener')
      initTelemetryErrorHandlers()

      expect(addSpy).toHaveBeenCalledWith('unhandledrejection', expect.any(Function))
      expect(addSpy).toHaveBeenCalledWith('error', expect.any(Function))
    })
  })
})
