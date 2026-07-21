/**
 * Traces API - Phase 8 Observability
 * Distributed tracing for workflow executions
 */

import { get } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const tracesAPI = {
  /**
   * Get list of traces with pagination
   * @param {Object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.limit - Items per page
   * @param {string} params.status - Filter by status
   * @param {string} params.workflowId - Filter by workflow
   * @param {string} params.startTime - Filter by start time
   * @param {string} params.endTime - Filter by end time
   * @returns {Promise<Object>} Paginated traces list
   */
  async getTraces(params = {}) {
    try {
      const result = await get(ENDPOINTS.TRACES.LIST, {
        params: {
          page: params.page || 1,
          limit: params.limit || 20,
          status: params.status,
          workflowId: params.workflowId,
          startTime: params.startTime,
          endTime: params.endTime
        }
      })

      return {
        ok: true,
        traces: (result.traces || []).map(t => ({
          traceId: t.traceId,
          executionId: t.executionId,
          workflowId: t.workflowId,
          workflowName: t.workflowName,
          status: t.status,
          durationMs: t.durationMs,
          spanCount: t.spanCount || 0,
          startedAt: t.startedAt,
          completedAt: t.completedAt,
          error: t.error
        })),
        pagination: {
          page: result.page || 1,
          limit: result.limit || 20,
          total: result.total || 0,
          totalPages: result.totalPages || 1
        }
      }
    } catch (err) {
      return {
        ok: false,
        error: err.message,
        traces: [],
        pagination: { page: 1, limit: 20, total: 0, totalPages: 1 }
      }
    }
  },

  /**
   * Get trace details by ID
   * @param {string} traceId - The trace ID
   * @returns {Promise<Object>} Trace details with spans
   */
  async getTrace(traceId) {
    try {
      const result = await get(ENDPOINTS.TRACES.GET(traceId))

      return {
        ok: true,
        trace: {
          traceId: result.traceId,
          executionId: result.executionId,
          workflowId: result.workflowId,
          workflowName: result.workflowName,
          status: result.status,
          durationMs: result.durationMs,
          startedAt: result.startedAt,
          completedAt: result.completedAt,
          error: result.error,
          metadata: result.metadata || {},
          spans: (result.spans || []).map(s => ({
            spanId: s.spanId,
            parentSpanId: s.parentSpanId,
            operationName: s.operationName,
            stepId: s.stepId,
            moduleId: s.moduleId,
            status: s.status,
            startTime: s.startTime,
            endTime: s.endTime,
            durationMs: s.durationMs,
            error: s.error,
            tags: s.tags || {},
            logs: s.logs || []
          }))
        }
      }
    } catch (err) {
      return { ok: false, error: err.message, trace: null }
    }
  },

  /**
   * Get spans for a specific trace with pre-computed tree and timeline data
   * S-Grade: Uses backend-computed values directly
   * @param {string} traceId - The trace ID
   * @returns {Promise<Object>} Spans with spanTree and timelineData
   */
  async getSpans(traceId) {
    try {
      const result = await get(ENDPOINTS.TRACES.SPANS(traceId))

      const spans = (result.spans || []).map(s => ({
        spanId: s.spanId,
        parentSpanId: s.parentSpanId,
        operationName: s.operationName,
        stepId: s.stepId,
        moduleId: s.moduleId,
        status: s.status,
        startTime: s.startTime,
        endTime: s.endTime,
        durationMs: s.durationMs,
        error: s.error,
        tags: s.tags || {},
        logs: s.logs || []
      }))

      return {
        ok: true,
        spans,
        // S-Grade: Use backend-computed values directly
        spanTree: result.spanTree || [],
        timelineData: result.timelineData || { spans: [], minTime: 0, maxTime: 0, totalDuration: 0 }
      }
    } catch (err) {
      return {
        ok: false,
        error: err.message,
        spans: [],
        spanTree: [],
        timelineData: { spans: [], minTime: 0, maxTime: 0, totalDuration: 0 }
      }
    }
  },

  /**
   * Search traces by various criteria
   * @param {Object} params - Search parameters
   * @param {string} params.query - Search query (trace ID, workflow name, etc.)
   * @param {string} params.status - Filter by status
   * @param {number} params.minDuration - Minimum duration in ms
   * @param {number} params.maxDuration - Maximum duration in ms
   * @param {string} params.startTime - Start time range
   * @param {string} params.endTime - End time range
   * @param {number} params.limit - Max results
   * @returns {Promise<Object>} Search results
   */
  async searchTraces(params = {}) {
    try {
      const result = await get(ENDPOINTS.TRACES.SEARCH, { params })

      return {
        ok: true,
        traces: (result.traces || []).map(t => ({
          traceId: t.traceId,
          executionId: t.executionId,
          workflowId: t.workflowId,
          workflowName: t.workflowName,
          status: t.status,
          durationMs: t.durationMs,
          spanCount: t.spanCount || 0,
          startedAt: t.startedAt,
          completedAt: t.completedAt,
          error: t.error
        })),
        total: result.total || 0
      }
    } catch (err) {
      return { ok: false, error: err.message, traces: [], total: 0 }
    }
  }
}

export default tracesAPI
