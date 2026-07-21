import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn()
}))

vi.mock('@/config/api', () => ({
  ENDPOINTS: {
    DEBUG: {
      HISTORY: (id) => `/api/debug/${id}/history`,
      STATS: (id) => `/api/debug/${id}/stats`,
      TIMELINE: (id) => `/api/debug/timeline/${id}`,
      NODE_DETAIL: (execId, nodeId) => `/api/debug/${execId}/nodes/${nodeId}`
    }
  }
}))

import { get } from '@/api/client'
import { useExecutionHistory } from '@/composables/useExecutionHistory'

describe('useExecutionHistory', () => {
  let history

  beforeEach(() => {
    vi.clearAllMocks()
    history = useExecutionHistory()
  })

  it('returns the expected API', () => {
    expect(history).toHaveProperty('executions')
    expect(history).toHaveProperty('loading')
    expect(history).toHaveProperty('error')
    expect(history).toHaveProperty('hasExecutions')
    expect(history).toHaveProperty('latestExecution')
    expect(history).toHaveProperty('successRate')
    expect(history).toHaveProperty('averageDuration')
    expect(history).toHaveProperty('executionsByStatus')
    expect(typeof history.fetchHistory).toBe('function')
    expect(typeof history.fetchStats).toBe('function')
    expect(typeof history.fetchTimeline).toBe('function')
    expect(typeof history.fetchNodeDetail).toBe('function')
    expect(typeof history.selectExecution).toBe('function')
    expect(typeof history.clearSelection).toBe('function')
    expect(typeof history.refresh).toBe('function')
    expect(typeof history.reset).toBe('function')
  })

  describe('initial state', () => {
    it('starts with no executions', () => {
      expect(history.hasExecutions.value).toBe(false)
      expect(history.latestExecution.value).toBeNull()
    })

    it('loading is false initially', () => {
      expect(history.loading.value).toBe(false)
    })

    it('error is null initially', () => {
      expect(history.error.value).toBeNull()
    })
  })

  describe('formatDuration', () => {
    it('returns "-" for null/undefined', () => {
      expect(history.formatDuration(null)).toBe('-')
      expect(history.formatDuration(undefined)).toBe('-')
    })

    it('formats milliseconds', () => {
      expect(history.formatDuration(500)).toBe('500ms')
    })

    it('formats seconds', () => {
      expect(history.formatDuration(2500)).toBe('2.5s')
    })

    it('formats minutes and seconds', () => {
      expect(history.formatDuration(125000)).toBe('2m 5s')
    })
  })

  describe('formatTime', () => {
    it('returns "-" for falsy input', () => {
      expect(history.formatTime(null)).toBe('-')
      expect(history.formatTime('')).toBe('-')
    })

    it('formats a valid timestamp', () => {
      const result = history.formatTime('2025-01-15T10:30:00Z')
      expect(result).toBeTruthy()
      expect(result).not.toBe('-')
    })
  })

  describe('normalizeStatus', () => {
    it('maps "completed" to "success"', () => {
      expect(history.normalizeStatus('completed')).toBe('success')
      expect(history.normalizeStatus('COMPLETED')).toBe('success')
    })

    it('maps "failure" and "error" to "failed"', () => {
      expect(history.normalizeStatus('failure')).toBe('failed')
      expect(history.normalizeStatus('error')).toBe('failed')
    })

    it('returns lowercase for other statuses', () => {
      expect(history.normalizeStatus('running')).toBe('running')
      expect(history.normalizeStatus('PENDING')).toBe('pending')
    })

    it('returns "unknown" for falsy input', () => {
      expect(history.normalizeStatus(null)).toBe('unknown')
      expect(history.normalizeStatus('')).toBe('unknown')
    })
  })

  describe('getStatusColor', () => {
    it('returns green for success', () => {
      expect(history.getStatusColor('success')).toBe('#10B981')
    })

    it('returns red for failed', () => {
      expect(history.getStatusColor('failed')).toBe('#ef4444')
    })

    it('returns fallback for unknown status', () => {
      expect(history.getStatusColor('xyz')).toBe('#64748b')
    })
  })

  describe('fetchHistory', () => {
    it('sets error when workflowId is missing', async () => {
      const result = await history.fetchHistory(null)
      expect(result).toEqual([])
      expect(history.error.value).toBe('Workflow ID is required')
    })

    it('fetches and normalizes executions', async () => {
      get.mockResolvedValue({
        executions: [
          { id: 'e1', status: 'completed', started_at: '2025-01-01T00:00:00Z', duration_ms: 1500 },
          { id: 'e2', status: 'failure', started_at: '2025-01-01T01:00:00Z', duration_ms: 300 }
        ]
      })

      const result = await history.fetchHistory('wf-1')
      expect(get).toHaveBeenCalled()
      expect(result).toHaveLength(2)
      expect(result[0].id).toBe('e1')
      expect(result[0].status).toBe('success')
      expect(result[1].status).toBe('failed')
      expect(history.hasExecutions.value).toBe(true)
      expect(history.latestExecution.value.id).toBe('e1')
    })

    it('handles API error gracefully', async () => {
      get.mockRejectedValue(new Error('Network error'))
      const result = await history.fetchHistory('wf-1')
      expect(result).toEqual([])
      expect(history.error.value).toBe('Network error')
    })

    it('sets loading state correctly', async () => {
      let resolvePromise
      get.mockReturnValue(new Promise(r => { resolvePromise = r }))

      const promise = history.fetchHistory('wf-1')
      expect(history.loading.value).toBe(true)

      resolvePromise({ executions: [] })
      await promise
      expect(history.loading.value).toBe(false)
    })
  })

  describe('fetchStats', () => {
    it('returns null when workflowId is missing', async () => {
      const result = await history.fetchStats(null)
      expect(result).toBeNull()
    })

    it('fetches and stores stats', async () => {
      const statsData = { success_rate: 95, average_duration_ms: 2000 }
      get.mockResolvedValue(statsData)

      const result = await history.fetchStats('wf-1')
      expect(result).toEqual(statsData)
      expect(history.successRate.value).toBe(95)
      expect(history.averageDuration.value).toBe(2000)
    })
  })

  describe('fetchTimeline', () => {
    it('returns null when executionId is missing', async () => {
      const result = await history.fetchTimeline(null)
      expect(result).toBeNull()
    })

    it('fetches and normalizes timeline', async () => {
      get.mockResolvedValue({
        execution_id: 'e1',
        workflow_id: 'wf-1',
        status: 'completed',
        duration_ms: 5000,
        total_steps: 3,
        completed_steps: 3,
        events: [
          { event_type: 'succeeded', node_id: 'n1', duration_ms: 200, timestamp: '2025-01-01T00:00:00Z' }
        ]
      })

      const result = await history.fetchTimeline('e1')
      expect(result).toBeTruthy()
      expect(result.executionId).toBe('e1')
      expect(result.status).toBe('success')
      expect(result.events).toHaveLength(1)
      expect(result.events[0].eventType).toBe('succeeded')
    })
  })

  describe('fetchNodeDetail', () => {
    it('returns null when params missing', async () => {
      expect(await history.fetchNodeDetail(null, 'n1')).toBeNull()
      expect(await history.fetchNodeDetail('e1', null)).toBeNull()
    })

    it('fetches and normalizes node detail', async () => {
      get.mockResolvedValue({
        node_id: 'n1',
        module_id: 'browser.click',
        status: 'success',
        duration_ms: 300,
        inputs: { selector: '#btn' },
        outputs: { clicked: true }
      })

      const result = await history.fetchNodeDetail('e1', 'n1')
      expect(result.nodeId).toBe('n1')
      expect(result.moduleId).toBe('browser.click')
      expect(result.inputs).toEqual({ selector: '#btn' })
    })
  })

  describe('executionsByStatus', () => {
    it('groups executions by status', async () => {
      get.mockResolvedValue({
        executions: [
          { id: 'e1', status: 'completed', started_at: '2025-01-01T00:00:00Z' },
          { id: 'e2', status: 'failure', started_at: '2025-01-01T01:00:00Z' },
          { id: 'e3', status: 'running', started_at: '2025-01-01T02:00:00Z' },
          { id: 'e4', status: 'cancelled', started_at: '2025-01-01T03:00:00Z' }
        ]
      })

      await history.fetchHistory('wf-1')
      const grouped = history.executionsByStatus.value
      expect(grouped.success).toHaveLength(1)
      expect(grouped.failed).toHaveLength(1)
      expect(grouped.running).toHaveLength(1)
      expect(grouped.cancelled).toHaveLength(1)
    })
  })

  describe('selectExecution', () => {
    it('sets selectedExecution and fetches timeline', async () => {
      get.mockResolvedValue({ execution_id: 'e1', status: 'success', events: [] })
      await history.selectExecution({ id: 'e1' })
      expect(history.selectedExecution.value).toEqual({ id: 'e1' })
      expect(get).toHaveBeenCalledWith(expect.stringContaining('e1'))
    })

    it('clears timeline when no execution', async () => {
      await history.selectExecution(null)
      expect(history.timeline.value).toBeNull()
    })
  })

  describe('clearSelection', () => {
    it('clears selected execution and timeline', async () => {
      get.mockResolvedValue({ execution_id: 'e1', status: 'success', events: [] })
      await history.selectExecution({ id: 'e1' })
      history.clearSelection()
      expect(history.selectedExecution.value).toBeNull()
      expect(history.timeline.value).toBeNull()
    })
  })

  describe('reset', () => {
    it('resets all state', async () => {
      get.mockResolvedValue({ executions: [{ id: 'e1', status: 'success', started_at: '' }] })
      await history.fetchHistory('wf-1')
      history.reset()
      expect(history.hasExecutions.value).toBe(false)
      expect(history.loading.value).toBe(false)
      expect(history.error.value).toBeNull()
      expect(history.selectedExecution.value).toBeNull()
    })
  })
})
