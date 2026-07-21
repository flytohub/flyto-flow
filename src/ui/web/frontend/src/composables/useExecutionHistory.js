/**
 * Execution History Composable
 *
 * Manages execution history data fetching and state for a workflow.
 * Provides timeline data, execution list, and statistics.
 *
 * SECURITY NOTE:
 * Status normalization and color mapping are for UI DISPLAY ONLY.
 * The authoritative execution status comes from the backend:
 * - Backend computes: status, duration, error info
 * - Backend provides: statusColor, formattedDuration (when available)
 *
 * Prefer using server-provided values:
 * - execution.computed_status (authoritative)
 * - execution.status_color (if provided)
 * - execution.formatted_duration (if provided)
 *
 * The local normalization is a fallback for backward compatibility.
 */
import { ref, computed, readonly } from 'vue'
import { get } from '@/api/client'
import { ENDPOINTS } from '@/config/api'

/**
 * Status color mapping (UI DISPLAY ONLY)
 *
 * SECURITY NOTE: These colors are for rendering only.
 * Backend provides authoritative status information.
 * Prefer using execution.status_color from backend when available.
 *
 * @deprecated Prefer using backend-provided status_color
 */
const STATUS_COLORS = {
  success: '#10B981',
  failed: '#ef4444',
  running: '#8B5CF6',
  pending: '#f59e0b',
  cancelled: '#6b7280',
  unknown: '#64748b'
}

/**
 * Event status color mapping (UI DISPLAY ONLY)
 *
 * @deprecated Prefer using backend-provided event_color
 */
const EVENT_COLORS = {
  succeeded: '#10B981',
  failed: '#ef4444',
  started: '#8B5CF6',
  skipped: '#f59e0b',
  cancelled: '#6b7280',
  unknown: '#64748b'
}

/**
 * Create execution history composable
 * @param {Object} options - Configuration options
 * @param {string} options.workflowId - Workflow ID to fetch history for
 * @returns {Object} Execution history state and methods
 */
export function useExecutionHistory(options = {}) {
  // ========== State ==========
  const executions = ref([])
  const selectedExecution = ref(null)
  const timeline = ref(null)
  const stats = ref(null)
  const loading = ref(false)
  const timelineLoading = ref(false)
  const error = ref(null)

  // ========== Computed ==========
  const hasExecutions = computed(() => executions.value.length > 0)

  const latestExecution = computed(() => {
    if (!executions.value.length) return null
    return executions.value[0]
  })

  const successRate = computed(() => {
    if (!stats.value) return null
    return stats.value.success_rate
  })

  const averageDuration = computed(() => {
    if (!stats.value) return null
    return stats.value.average_duration_ms
  })

  /**
   * Group executions by status
   *
   * Uses backend-provided statusGroup when available,
   * falls back to local normalization for backward compatibility.
   */
  const executionsByStatus = computed(() => {
    const grouped = {
      success: [],
      failed: [],
      running: [],
      cancelled: [],
      other: []
    }

    executions.value.forEach(exec => {
      const group = exec.statusGroup || normalizeStatusGroup(exec.status)
      if (grouped[group]) {
        grouped[group].push(exec)
      } else {
        grouped.other.push(exec)
      }
    })

    return grouped
  })

  /**
   * Map a raw status string to a status group.
   * Fallback for when backend doesn't provide statusGroup.
   */
  function normalizeStatusGroup(status) {
    const s = (status || '').toLowerCase()
    if (s === 'success' || s === 'completed') return 'success'
    if (s === 'failed' || s === 'failure' || s === 'error') return 'failed'
    if (s === 'running' || s === 'pending') return 'running'
    if (s === 'cancelled') return 'cancelled'
    return 'other'
  }

  // ========== Actions ==========

  /**
   * Fetch execution history for a workflow
   * @param {string} workflowId - Workflow ID
   * @param {Object} options - Fetch options
   * @param {number} options.limit - Max number of executions to fetch
   * @param {string} options.status - Filter by status
   * @returns {Promise<Array>} Execution list
   */
  async function fetchHistory(workflowId, { limit = 20, status = null } = {}) {
    if (!workflowId) {
      error.value = 'Workflow ID is required'
      return []
    }

    loading.value = true
    error.value = null

    try {
      let url = ENDPOINTS.DEBUG.HISTORY(workflowId)
      const params = new URLSearchParams()
      if (limit) params.append('limit', limit.toString())
      if (status) params.append('status', status)
      if (params.toString()) url += `?${params.toString()}`

      const response = await get(url)

      if (response.executions) {
        executions.value = response.executions.map(normalizeExecution)
      }

      return executions.value
    } catch (err) {
      error.value = err.userMessage || err.message || 'Failed to fetch execution history'
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch execution statistics for a workflow
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<Object>} Statistics object
   */
  async function fetchStats(workflowId) {
    if (!workflowId) {
      error.value = 'Workflow ID is required'
      return null
    }

    try {
      const response = await get(ENDPOINTS.DEBUG.STATS(workflowId))
      stats.value = response
      return response
    } catch (err) {
      // Stats fetch failure is not critical
      return null
    }
  }

  /**
   * Fetch detailed timeline for an execution
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Timeline data
   */
  async function fetchTimeline(executionId) {
    if (!executionId) {
      error.value = 'Execution ID is required'
      return null
    }

    timelineLoading.value = true

    try {
      const response = await get(ENDPOINTS.DEBUG.TIMELINE(executionId))
      timeline.value = normalizeTimeline(response)
      return timeline.value
    } catch (err) {
      error.value = err.userMessage || err.message || 'Failed to fetch execution timeline'
      return null
    } finally {
      timelineLoading.value = false
    }
  }

  /**
   * Fetch node detail for an execution
   * @param {string} executionId - Execution ID
   * @param {string} nodeId - Node ID
   * @returns {Promise<Object>} Node detail
   */
  async function fetchNodeDetail(executionId, nodeId) {
    if (!executionId || !nodeId) {
      error.value = 'Execution ID and Node ID are required'
      return null
    }

    try {
      const response = await get(ENDPOINTS.DEBUG.NODE_DETAIL(executionId, nodeId))
      return normalizeNodeDetail(response)
    } catch (err) {
      error.value = err.userMessage || err.message || 'Failed to fetch node detail'
      return null
    }
  }

  /**
   * Select an execution and load its timeline
   * @param {Object} execution - Execution object
   */
  async function selectExecution(execution) {
    selectedExecution.value = execution
    if (execution?.id) {
      await fetchTimeline(execution.id)
    } else {
      timeline.value = null
    }
  }

  /**
   * Clear selection
   */
  function clearSelection() {
    selectedExecution.value = null
    timeline.value = null
  }

  /**
   * Refresh current data
   * @param {string} workflowId - Workflow ID
   */
  async function refresh(workflowId) {
    if (!workflowId) return

    await Promise.all([
      fetchHistory(workflowId),
      fetchStats(workflowId)
    ])

    // Refresh selected execution timeline if any
    if (selectedExecution.value?.id) {
      await fetchTimeline(selectedExecution.value.id)
    }
  }

  /**
   * Reset state
   */
  function reset() {
    executions.value = []
    selectedExecution.value = null
    timeline.value = null
    stats.value = null
    loading.value = false
    timelineLoading.value = false
    error.value = null
  }

  // ========== Helpers ==========

  /**
   * Normalize execution data
   *
   * Prefers backend-computed values (status_color, formatted_duration)
   * when available, falls back to local computation for backward compatibility.
   */
  function normalizeExecution(exec) {
    return {
      id: exec.id,
      status: normalizeStatus(exec.status),
      startedAt: exec.startedAt ?? exec.started_at,
      finishedAt: exec.finishedAt ?? exec.finished_at,
      durationMs: exec.durationMs ?? exec.duration_ms,
      errorMessage: exec.errorMessage ?? exec.error_message,
      // Prefer backend-computed values, fallback to local
      formattedDuration: (exec.formattedDuration ?? exec.formatted_duration) || formatDuration(exec.durationMs ?? exec.duration_ms),
      formattedStartTime: formatTime(exec.startedAt ?? exec.started_at),
      statusColor: (exec.statusColor ?? exec.status_color) || getStatusColor(exec.status)
    }
  }

  /**
   * Normalize timeline data
   */
  function normalizeTimeline(data) {
    if (!data) return null

    return {
      executionId: data.executionId ?? data.execution_id,
      workflowId: data.workflowId ?? data.workflow_id,
      workflowName: data.workflowName ?? data.workflow_name,
      status: normalizeStatus(data.status),
      startedAt: data.startedAt ?? data.started_at,
      finishedAt: data.finishedAt ?? data.finished_at,
      durationMs: data.durationMs ?? data.duration_ms,
      totalSteps: data.totalSteps ?? data.total_steps,
      completedSteps: data.completedSteps ?? data.completed_steps,
      failedStep: data.failedStep ?? data.failed_step,
      events: (data.events || []).map(normalizeEvent),
      contextSnapshots: data.contextSnapshots ?? data.context_snapshots ?? {},
      // Prefer backend-computed values
      formattedDuration: (data.formattedDuration ?? data.formatted_duration) || formatDuration(data.durationMs ?? data.duration_ms),
      statusColor: (data.statusColor ?? data.status_color) || getStatusColor(data.status)
    }
  }

  /**
   * Normalize event data
   */
  function normalizeEvent(event) {
    return {
      timestamp: event.timestamp,
      eventType: event.eventType ?? event.event_type,
      nodeId: event.nodeId ?? event.node_id,
      nodeRunId: event.nodeRunId ?? event.node_run_id,
      stepIndex: event.stepIndex ?? event.step_index,
      moduleId: event.moduleId ?? event.module_id,
      durationMs: event.durationMs ?? event.duration_ms,
      inputs: event.inputs,
      outputs: event.outputs,
      error: event.error,
      errorCategory: event.errorCategory ?? event.error_category,
      // Prefer backend-computed values
      formattedDuration: (event.formattedDuration ?? event.formatted_duration) || formatDuration(event.durationMs ?? event.duration_ms),
      formattedTime: formatTime(event.timestamp),
      statusColor: (event.eventColor ?? event.event_color) || getEventStatusColor(event.eventType ?? event.event_type)
    }
  }

  /**
   * Normalize node detail data
   */
  function normalizeNodeDetail(data) {
    if (!data) return null

    return {
      nodeId: data.nodeId ?? data.node_id,
      moduleId: data.moduleId ?? data.module_id,
      status: data.status,
      startedAt: data.startedAt ?? data.started_at,
      finishedAt: data.finishedAt ?? data.finished_at,
      durationMs: data.durationMs ?? data.duration_ms,
      inputs: data.inputs,
      outputs: data.outputs,
      error: data.error,
      errorCategory: data.errorCategory ?? data.error_category,
      stackTrace: data.stackTrace ?? data.stack_trace,
      contextBefore: data.contextBefore ?? data.context_before,
      // Prefer backend-computed values
      formattedDuration: (data.formattedDuration ?? data.formatted_duration) || formatDuration(data.durationMs ?? data.duration_ms)
    }
  }

  /**
   * Normalize status string (UI DISPLAY ONLY)
   *
   * Maps various status strings to canonical form for display.
   * Backend status is authoritative; this is for UI consistency.
   */
  function normalizeStatus(status) {
    if (!status) return 'unknown'
    const s = status.toLowerCase()
    if (s === 'completed' || s === 'success') return 'success'
    if (s === 'failure' || s === 'error') return 'failed'
    return s
  }

  /**
   * Get status color (UI DISPLAY ONLY)
   *
   * SECURITY NOTE: For rendering only. Prefer backend-provided status_color.
   * @deprecated Use backend-provided status_color when available
   */
  function getStatusColor(status) {
    const s = normalizeStatus(status)
    return STATUS_COLORS[s] || STATUS_COLORS.unknown
  }

  /**
   * Get event status color (UI DISPLAY ONLY)
   *
   * @deprecated Use backend-provided event_color when available
   */
  function getEventStatusColor(eventType) {
    return EVENT_COLORS[eventType] || EVENT_COLORS.unknown
  }

  /**
   * Format duration (UI DISPLAY ONLY)
   *
   * Prefer backend-provided formatted_duration when available.
   */
  function formatDuration(ms) {
    if (ms === null || ms === undefined) return '-'
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    const minutes = Math.floor(ms / 60000)
    const seconds = Math.floor((ms % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  }

  /**
   * Format timestamp (UI DISPLAY ONLY)
   */
  function formatTime(timestamp) {
    if (!timestamp) return '-'
    try {
      const date = new Date(timestamp)
      return date.toLocaleString()
    } catch {
      return timestamp
    }
  }

  // ========== Return ==========
  return {
    // State (readonly)
    executions: readonly(executions),
    selectedExecution: readonly(selectedExecution),
    timeline: readonly(timeline),
    stats: readonly(stats),
    loading: readonly(loading),
    timelineLoading: readonly(timelineLoading),
    error: readonly(error),

    // Computed
    hasExecutions,
    latestExecution,
    successRate,
    averageDuration,
    executionsByStatus,

    // Actions
    fetchHistory,
    fetchStats,
    fetchTimeline,
    fetchNodeDetail,
    selectExecution,
    clearSelection,
    refresh,
    reset,

    // Utilities (UI display only)
    formatDuration,
    formatTime,
    getStatusColor,
    normalizeStatus
  }
}

export default useExecutionHistory
