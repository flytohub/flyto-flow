import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/executions', () => ({
  pauseExecution: vi.fn(),
  resumeExecution: vi.fn(),
  stepExecution: vi.fn(),
  getExecutionState: vi.fn(),
  getResumeOptions: vi.fn(),
  resumeFromCheckpoint: vi.fn(),
}))

vi.mock('@/services/telemetry', () => ({
  telemetry: { track: vi.fn() }
}))

import { useExecutionControlStore } from '@/stores/execution/executionControlStoreCore'
import * as executionAPI from '@/api/executions'

describe('useExecutionControlStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useExecutionControlStore()
    vi.clearAllMocks()
  })

  // ==========================================================================
  // Initial State
  // ==========================================================================
  describe('initial state', () => {
    it('has correct defaults', () => {
      expect(store.executionId).toBeNull()
      expect(store.status).toBe('idle')
      expect(store.currentState).toBeNull()
      expect(store.resumeOptions).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  // ==========================================================================
  // Getters
  // ==========================================================================
  describe('getters', () => {
    it('isPaused when status is paused', () => {
      store.setExecution('exec-1', 'paused')
      expect(store.isPaused).toBe(true)
      expect(store.isRunning).toBe(false)
    })

    it('isRunning when status is running', () => {
      store.setExecution('exec-1', 'running')
      expect(store.isRunning).toBe(true)
      expect(store.isPaused).toBe(false)
    })

    it('isStepping when status is stepping', () => {
      store.setExecution('exec-1', 'stepping')
      expect(store.isStepping).toBe(true)
    })

    it('isPausedAtCheckpoint when status is paused_at_checkpoint', () => {
      store.setExecution('exec-1', 'paused_at_checkpoint')
      expect(store.isPausedAtCheckpoint).toBe(true)
    })

    it('canPause only when running', () => {
      store.setExecution('exec-1', 'running')
      expect(store.canPause).toBe(true)

      store.updateStatus('paused')
      expect(store.canPause).toBe(false)
    })

    it('canResume when paused or paused_at_checkpoint', () => {
      store.setExecution('exec-1', 'paused')
      expect(store.canResume).toBe(true)

      store.updateStatus('paused_at_checkpoint')
      expect(store.canResume).toBe(true)

      store.updateStatus('running')
      expect(store.canResume).toBe(false)
    })

    it('canStep only when paused', () => {
      store.setExecution('exec-1', 'paused')
      expect(store.canStep).toBe(true)

      store.updateStatus('running')
      expect(store.canStep).toBe(false)
    })

    it('hasResumeOptions checks canResume flag', () => {
      expect(store.hasResumeOptions).toBe(false)

      store.resumeOptions = { canResume: true }
      expect(store.hasResumeOptions).toBe(true)
    })

    it('checkpoints extracts from resumeOptions', () => {
      expect(store.checkpoints).toEqual([])

      store.resumeOptions = { checkpoints: ['cp1', 'cp2'] }
      expect(store.checkpoints).toEqual(['cp1', 'cp2'])
    })

    it('recommendedCheckpoint extracts from resumeOptions', () => {
      expect(store.recommendedCheckpoint).toBeNull()

      store.resumeOptions = { recommendedCheckpoint: 'cp1' }
      expect(store.recommendedCheckpoint).toBe('cp1')
    })

    it('failureInfo extracts from resumeOptions', () => {
      expect(store.failureInfo).toBeNull()

      store.resumeOptions = { failureNode: 'node-1', failureMessage: 'Timeout' }
      expect(store.failureInfo).toEqual({ node: 'node-1', message: 'Timeout' })
    })
  })

  // ==========================================================================
  // setExecution
  // ==========================================================================
  describe('setExecution', () => {
    it('sets execution id and status', () => {
      store.setExecution('exec-1', 'running')

      expect(store.executionId).toBe('exec-1')
      expect(store.status).toBe('running')
      expect(store.currentState).toBeNull()
      expect(store.resumeOptions).toBeNull()
      expect(store.error).toBeNull()
    })

    it('defaults status to running', () => {
      store.setExecution('exec-1')
      expect(store.status).toBe('running')
    })
  })

  // ==========================================================================
  // pause
  // ==========================================================================
  describe('pause', () => {
    it('pauses execution on success', async () => {
      store.setExecution('exec-1', 'running')
      executionAPI.pauseExecution.mockResolvedValue({ ok: true })
      executionAPI.getExecutionState.mockResolvedValue({ ok: true, variables: {} })

      const result = await store.pause()

      expect(result).toBe(true)
      expect(store.status).toBe('paused')
      expect(executionAPI.pauseExecution).toHaveBeenCalledWith('exec-1', 'user_request')
    })

    it('passes custom reason', async () => {
      store.setExecution('exec-1', 'running')
      executionAPI.pauseExecution.mockResolvedValue({ ok: true })
      executionAPI.getExecutionState.mockResolvedValue({ ok: true, variables: {} })

      await store.pause('debug')

      expect(executionAPI.pauseExecution).toHaveBeenCalledWith('exec-1', 'debug')
    })

    it('does nothing when not running', async () => {
      store.setExecution('exec-1', 'paused')

      const result = await store.pause()

      expect(result).toBe(false)
      expect(executionAPI.pauseExecution).not.toHaveBeenCalled()
    })

    it('does nothing without execution id', async () => {
      const result = await store.pause()

      expect(result).toBe(false)
    })

    it('sets error on failure', async () => {
      store.setExecution('exec-1', 'running')
      executionAPI.pauseExecution.mockRejectedValue({ message: 'Server error' })

      const result = await store.pause()

      expect(result).toBe(false)
      expect(store.error).toBe('Server error')
    })
  })

  // ==========================================================================
  // resume
  // ==========================================================================
  describe('resume', () => {
    it('resumes execution on success', async () => {
      store.setExecution('exec-1', 'paused')
      executionAPI.resumeExecution.mockResolvedValue({ ok: true })

      const result = await store.resume()

      expect(result).toBe(true)
      expect(store.status).toBe('running')
    })

    it('does nothing when not pausable', async () => {
      store.setExecution('exec-1', 'running')

      const result = await store.resume()

      expect(result).toBe(false)
    })

    it('sets error on failure', async () => {
      store.setExecution('exec-1', 'paused')
      executionAPI.resumeExecution.mockRejectedValue({ userMessage: 'Cannot resume' })

      const result = await store.resume()

      expect(result).toBe(false)
      expect(store.error).toBe('Cannot resume')
    })
  })

  // ==========================================================================
  // step
  // ==========================================================================
  describe('step', () => {
    it('steps execution and returns to paused', async () => {
      store.setExecution('exec-1', 'paused')
      executionAPI.stepExecution.mockResolvedValue({ ok: true })
      executionAPI.getExecutionState.mockResolvedValue({ ok: true, variables: {} })

      const result = await store.step()

      expect(result).toBe(true)
      expect(store.status).toBe('paused')
    })

    it('does nothing when not paused', async () => {
      store.setExecution('exec-1', 'running')

      const result = await store.step()

      expect(result).toBe(false)
    })

    it('reverts to paused on error', async () => {
      store.setExecution('exec-1', 'paused')
      executionAPI.stepExecution.mockRejectedValue({ message: 'Step failed' })

      const result = await store.step()

      expect(result).toBe(false)
      expect(store.status).toBe('paused')
      expect(store.error).toBe('Step failed')
    })
  })

  // ==========================================================================
  // fetchState
  // ==========================================================================
  describe('fetchState', () => {
    it('fetches and stores state', async () => {
      store.setExecution('exec-1')
      executionAPI.getExecutionState.mockResolvedValue({
        ok: true,
        variables: { node1: { output: 'data', status: 'completed' } },
        nodeOutputs: { node2: 'raw-data' }
      })

      const result = await store.fetchState()

      expect(result.ok).toBe(true)
      expect(store.currentState).toBeTruthy()
    })

    it('returns null without execution id', async () => {
      const result = await store.fetchState()
      expect(result).toBeNull()
    })

    it('sets error on failure', async () => {
      store.setExecution('exec-1')
      executionAPI.getExecutionState.mockRejectedValue({ message: 'Not found' })

      const result = await store.fetchState()

      expect(result).toBeNull()
      expect(store.error).toBe('Not found')
    })
  })

  // ==========================================================================
  // fetchResumeOptions
  // ==========================================================================
  describe('fetchResumeOptions', () => {
    it('stores resume options on success', async () => {
      store.setExecution('exec-1')
      const mockOptions = { canResume: true, checkpoints: ['cp1'] }
      executionAPI.getResumeOptions.mockResolvedValue({ ok: true, options: mockOptions })

      const result = await store.fetchResumeOptions()

      expect(result).toEqual(mockOptions)
      expect(store.resumeOptions).toEqual(mockOptions)
    })

    it('returns null without execution id', async () => {
      const result = await store.fetchResumeOptions()
      expect(result).toBeNull()
    })
  })

  // ==========================================================================
  // resumeFromCheckpoint
  // ==========================================================================
  describe('resumeFromCheckpoint', () => {
    it('resumes from checkpoint and updates execution id', async () => {
      store.setExecution('exec-1', 'paused')
      store.resumeOptions = { canResume: true }

      executionAPI.resumeFromCheckpoint.mockResolvedValue({
        ok: true,
        newExecutionId: 'exec-2'
      })

      const result = await store.resumeFromCheckpoint('cp-1', { var1: 'changed' })

      expect(result.ok).toBe(true)
      expect(store.executionId).toBe('exec-2')
      expect(store.status).toBe('running')
      expect(store.resumeOptions).toBeNull()
      expect(store.currentState).toBeNull()
    })

    it('returns null without execution id', async () => {
      const result = await store.resumeFromCheckpoint('cp-1')
      expect(result).toBeNull()
    })

    it('returns error result on failure', async () => {
      store.setExecution('exec-1')
      executionAPI.resumeFromCheckpoint.mockRejectedValue({ message: 'Checkpoint not found' })

      const result = await store.resumeFromCheckpoint('cp-bad')

      expect(result).toEqual({ ok: false, error: 'Checkpoint not found' })
    })
  })

  // ==========================================================================
  // updateStatus & clearError
  // ==========================================================================
  describe('updateStatus', () => {
    it('updates the status', () => {
      store.updateStatus('paused')
      expect(store.status).toBe('paused')
    })
  })

  describe('clearError', () => {
    it('clears error', () => {
      store.error = 'some error'
      store.clearError()
      expect(store.error).toBeNull()
    })
  })

  // ==========================================================================
  // reset
  // ==========================================================================
  describe('reset', () => {
    it('resets all state to defaults', () => {
      store.setExecution('exec-1', 'running')
      store.error = 'err'

      store.reset()

      expect(store.executionId).toBeNull()
      expect(store.status).toBe('idle')
      expect(store.currentState).toBeNull()
      expect(store.resumeOptions).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })
})
