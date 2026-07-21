import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPollingActions } from '@/composables/templateBuilder/templateExecution/pollingActions'

// Mock dependencies
vi.mock('@/api/executions', () => ({
  getExecutionStatus: vi.fn()
}))
vi.mock('@/api/jobs', () => ({
  getJobState: vi.fn()
}))
vi.mock('@/stores/execution/nodeOutputStore', () => ({
  useNodeOutputStore: vi.fn(() => ({
    updateDisplayOutputsFromList: vi.fn(),
    getNodeOutputInfo: vi.fn(() => null),
    setNodeOutput: vi.fn(),
    hasOutput: vi.fn(() => false)
  }))
}))
vi.mock('@/composables/useToast', () => ({
  useToast: vi.fn(() => ({
    error: vi.fn(),
    success: vi.fn()
  }))
}))
vi.mock('@/config/api', () => ({
  getWsUrl: vi.fn(() => 'ws://localhost:8000')
}))

// Stub WebSocket globally
class MockWebSocket {
  constructor() {
    this.onmessage = null
    this.onclose = null
    this.onerror = null
  }
  close() {}
}
globalThis.WebSocket = MockWebSocket

import * as executionAPI from '@/api/executions'
import * as jobsAPI from '@/api/jobs'

function createMockState() {
  return {
    isExecuting: { value: true },
    currentExecutionId: { value: 'exec-123' },
    executionStatus: { value: 'running' },
    executionNodeStates: { value: {} },
    executionNodeTimings: { value: {} },
    executionNodeInputs: { value: {} },
    executionNodeOutputs: { value: {} },
    executionActiveNodeId: { value: null },
    executionCompletedNodeIds: { value: [] },
    executionProgress: { value: { current: 0, total: 0, percent: 0 } },
    executionDisplayOutputs: { value: [] },
    hasBrowser: { value: false },
    agentActivity: { value: {} }
  }
}

function createMockControlStore() {
  return {
    setExecution: vi.fn(),
    fetchState: vi.fn(),
    fetchResumeOptions: vi.fn()
  }
}

describe('createPollingActions', () => {
  let state, controlStore, actions

  beforeEach(() => {
    vi.useFakeTimers()
    state = createMockState()
    controlStore = createMockControlStore()
    actions = createPollingActions(state, controlStore)
  })

  afterEach(() => {
    actions.setUnmounted()
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('returns expected action functions', () => {
    expect(actions).toHaveProperty('startExecutionPolling')
    expect(actions).toHaveProperty('startJobPolling')
    expect(actions).toHaveProperty('stopExecutionPolling')
    expect(actions).toHaveProperty('resetExecutionState')
    expect(actions).toHaveProperty('setUnmounted')
  })

  it('resetExecutionState clears all state', () => {
    state.isExecuting.value = true
    state.executionNodeStates.value = { n1: 'completed' }
    state.executionActiveNodeId.value = 'n1'

    actions.resetExecutionState()

    expect(state.isExecuting.value).toBe(false)
    expect(state.executionNodeStates.value).toEqual({})
    expect(state.executionActiveNodeId.value).toBeNull()
    expect(state.executionCompletedNodeIds.value).toEqual([])
  })

  describe('polling lifecycle', () => {
    it('startExecutionPolling schedules a poll', () => {
      executionAPI.getExecutionStatus.mockResolvedValue({
        ok: true,
        status: 'running',
        nodeStates: {},
        nodeTimings: {},
        nodeInputs: {},
        nodeOutputs: {},
        completedNodeIds: [],
        progress: { current: 1, total: 5, percent: 20 },
        displayOutputs: []
      })

      actions.startExecutionPolling()
      // Should have scheduled a timeout
      vi.advanceTimersByTime(500)

      expect(executionAPI.getExecutionStatus).toHaveBeenCalledWith('exec-123')
    })

    it('startJobPolling uses job API', async () => {
      jobsAPI.getJobState.mockResolvedValue({
        ok: true,
        status: 'running',
        nodeStates: {},
        nodeTimings: {},
        nodeInputs: {},
        nodeOutputs: {},
        completedNodeIds: [],
        progress: { current: 0, total: 0, percent: 0 },
        displayOutputs: []
      })

      actions.startJobPolling('job-456')
      vi.advanceTimersByTime(1000)

      expect(jobsAPI.getJobState).toHaveBeenCalledWith('job-456')
    })

    it('sets hasBrowser=false when starting job polling (waits for backend browser_available)', () => {
      jobsAPI.getJobState.mockResolvedValue({
        ok: true, status: 'running', nodeStates: {}, nodeTimings: {},
        nodeInputs: {}, nodeOutputs: {}, completedNodeIds: [],
        progress: { current: 0, total: 0, percent: 0 }, displayOutputs: []
      })

      actions.startJobPolling('job-456')
      expect(state.hasBrowser.value).toBe(false)
    })
  })

  describe('terminal status handling', () => {
    it('handles completed status', async () => {
      executionAPI.getExecutionStatus.mockResolvedValue({
        ok: true,
        status: 'completed',
        nodeStates: { n1: 'completed' },
        nodeTimings: {},
        nodeInputs: {},
        nodeOutputs: {},
        activeNodeId: null,
        completedNodeIds: ['n1'],
        progress: { current: 5, total: 5, percent: 100 },
        displayOutputs: []
      })

      actions.startExecutionPolling()
      vi.advanceTimersByTime(500)
      await vi.runAllTimersAsync()

      expect(controlStore.setExecution).toHaveBeenCalledWith('exec-123', 'completed')
      expect(state.isExecuting.value).toBe(false)
    })

    it('handles failed status with toast', async () => {
      executionAPI.getExecutionStatus.mockResolvedValue({
        ok: true,
        status: 'failed',
        error: 'Something went wrong',
        nodeStates: {},
        nodeTimings: {},
        nodeInputs: {},
        nodeOutputs: {},
        activeNodeId: null,
        completedNodeIds: [],
        progress: { current: 0, total: 0, percent: 0 },
        displayOutputs: []
      })

      actions.startExecutionPolling()
      vi.advanceTimersByTime(500)
      await vi.runAllTimersAsync()

      expect(controlStore.setExecution).toHaveBeenCalledWith('exec-123', 'failed')
      expect(controlStore.fetchResumeOptions).toHaveBeenCalled()
      expect(state.isExecuting.value).toBe(false)
    })

    it('handles cancelled status', async () => {
      executionAPI.getExecutionStatus.mockResolvedValue({
        ok: true,
        status: 'cancelled',
        nodeStates: {},
        nodeTimings: {},
        nodeInputs: {},
        nodeOutputs: {},
        activeNodeId: null,
        completedNodeIds: [],
        progress: { current: 0, total: 0, percent: 0 },
        displayOutputs: []
      })

      actions.startExecutionPolling()
      vi.advanceTimersByTime(500)
      await vi.runAllTimersAsync()

      expect(state.isExecuting.value).toBe(false)
    })
  })

  describe('error handling', () => {
    it('backs off on poll errors', async () => {
      // First call succeeds, second fails
      executionAPI.getExecutionStatus
        .mockResolvedValueOnce({ ok: false })

      actions.startExecutionPolling()
      await vi.advanceTimersByTimeAsync(500)

      // Should have been called once and scheduled next poll with backoff
      expect(executionAPI.getExecutionStatus).toHaveBeenCalledTimes(1)
    })

    it('resets on 404 error', async () => {
      executionAPI.getExecutionStatus.mockRejectedValue({
        response: { status: 404 }
      })

      actions.startExecutionPolling()
      vi.advanceTimersByTime(500)
      await vi.runAllTimersAsync()

      expect(state.isExecuting.value).toBe(false)
    })
  })

  describe('state updates from poll data', () => {
    it('updates execution state from poll response', async () => {
      executionAPI.getExecutionStatus.mockResolvedValue({
        ok: true,
        status: 'running',
        nodeStates: { n1: 'completed', n2: 'running' },
        nodeTimings: { n1: { durationMs: 1200, startedAt: '2026-01-01' } },
        nodeInputs: { n1: { url: 'https://example.com' } },
        nodeOutputs: { n1: { result: 'ok' } },
        activeNodeId: 'n2',
        completedNodeIds: ['n1'],
        progress: { current: 1, total: 3, percent: 33 },
        displayOutputs: [{ nodeId: 'n1', output: 'ok' }],
        hasBrowser: true
      })

      actions.startExecutionPolling()
      await vi.advanceTimersByTimeAsync(500)

      expect(state.executionNodeStates.value).toEqual({ n1: 'completed', n2: 'running' })
      expect(state.executionActiveNodeId.value).toBe('n2')
      expect(state.executionCompletedNodeIds.value).toEqual(['n1'])
      expect(state.executionProgress.value).toEqual({ current: 1, total: 3, percent: 33 })
      expect(state.hasBrowser.value).toBe(true)
    })
  })
})
