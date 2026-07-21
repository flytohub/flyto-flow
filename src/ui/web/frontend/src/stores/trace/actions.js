/**
 * Trace Store Actions
 *
 * S-Grade: Trace operations.
 * Single responsibility: Fetch and manage traces and spans.
 */

import { tracesAPI } from '@/api/traces'
import i18n from '@/i18n'
import { asObject, asRecordArray, asNonNegativeInteger } from '@/utils/dataBoundary'

/**
 * Create trace fetch actions
 * @param {Object} state - State refs
 * @returns {Object} Action functions
 */
export function createTraceActions(state) {
  const {
    traces,
    currentTrace,
    spans,
    spanTree,
    timelineData,
    pagination,
    filters,
    isLoading,
    isLoadingTrace,
    error
  } = state

  /**
   * Fetch traces list with pagination
   */
  async function fetchTraces(params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const result = await tracesAPI.getTraces({
        page: params.page || pagination.value.page,
        limit: params.limit || pagination.value.limit,
        status: params.status || filters.value.status,
        workflowId: params.workflowId || filters.value.workflowId,
        startTime: params.startTime || filters.value.startTime,
        endTime: params.endTime || filters.value.endTime
      })

      const normalized = asObject(result)
      if (normalized.ok) {
        traces.value = asRecordArray(normalized.traces)
        pagination.value = {
          ...asObject(pagination.value),
          ...asObject(normalized.pagination)
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchTraces')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch single trace details
   */
  async function fetchTrace(traceId) {
    isLoadingTrace.value = true
    error.value = null

    try {
      const result = await tracesAPI.getTrace(traceId)

      const normalized = asObject(result)
      if (normalized.ok) {
        const trace = asObject(normalized.trace)
        currentTrace.value = Object.keys(trace).length > 0 ? trace : null
        spans.value = asRecordArray(trace.spans)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchTrace')
      return { ok: false, error: error.value }
    } finally {
      isLoadingTrace.value = false
    }
  }

  /**
   * Fetch spans for a trace with pre-computed tree and timeline data
   * S-Grade: Uses backend-computed values directly
   */
  async function fetchSpans(traceId) {
    isLoadingTrace.value = true
    error.value = null

    try {
      const result = await tracesAPI.getSpans(traceId)

      const normalized = asObject(result)
      if (normalized.ok) {
        spans.value = asRecordArray(normalized.spans)
        // S-Grade: Direct assignment from backend (no frontend computation)
        spanTree.value = asObject(normalized.spanTree)
        timelineData.value = asObject(normalized.timelineData)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchSpans')
      return { ok: false, error: error.value }
    } finally {
      isLoadingTrace.value = false
    }
  }

  /**
   * Search traces
   */
  async function searchTraces(query) {
    isLoading.value = true
    error.value = null
    filters.value.query = query

    try {
      const result = await tracesAPI.searchTraces({
        query,
        status: filters.value.status,
        startTime: filters.value.startTime,
        endTime: filters.value.endTime,
        limit: pagination.value.limit
      })

      const normalized = asObject(result)
      if (normalized.ok) {
        traces.value = asRecordArray(normalized.traces)
        pagination.value.total = asNonNegativeInteger(normalized.total, traces.value.length)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToSearchTraces')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    fetchTraces,
    fetchTrace,
    fetchSpans,
    searchTraces,
  }
}

/**
 * Create utility actions
 * @param {Object} state - State refs
 * @param {Function} fetchTraces - Fetch traces function
 * @returns {Object} Utility action functions
 */
export function createUtilityActions(state, fetchTraces) {
  const {
    traces,
    currentTrace,
    spans,
    spanTree,
    timelineData,
    selectedSpan,
    pagination,
    filters,
    isLoading,
    isLoadingTrace,
    error
  } = state

  /**
   * Set page and fetch
   */
  async function setPage(page) {
    pagination.value.page = page
    await fetchTraces({ page })
  }

  /**
   * Set filters and fetch
   */
  async function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1
    await fetchTraces()
  }

  /**
   * Select a span for detail view
   */
  function selectSpan(span) {
    selectedSpan.value = span
  }

  /**
   * Clear current trace
   */
  function clearCurrentTrace() {
    currentTrace.value = null
    spans.value = []
    spanTree.value = []
    timelineData.value = { spans: [], minTime: 0, maxTime: 0, totalDuration: 0 }
    selectedSpan.value = null
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset state
   */
  function reset() {
    traces.value = []
    currentTrace.value = null
    spans.value = []
    spanTree.value = []
    timelineData.value = { spans: [], minTime: 0, maxTime: 0, totalDuration: 0 }
    selectedSpan.value = null
    pagination.value = { page: 1, limit: 20, total: 0, totalPages: 1 }
    filters.value = { status: null, workflowId: null, startTime: null, endTime: null, query: '' }
    isLoading.value = false
    isLoadingTrace.value = false
    error.value = null
  }

  return {
    setPage,
    setFilters,
    selectSpan,
    clearCurrentTrace,
    clearError,
    reset,
  }
}
