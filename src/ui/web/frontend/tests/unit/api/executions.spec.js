import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

vi.mock('@/api/config', () => ({
  ENDPOINTS: {
    EXECUTIONS: {
      GET: (id) => `/executions/${id}`,
      PAUSE: (id) => `/executions/${id}/pause`,
      RESUME: (id) => `/executions/${id}/resume`,
      STEP: (id) => `/executions/${id}/step`,
      STATE: (id) => `/executions/${id}/state`,
      RUN_TO_END: (id) => `/executions/${id}/run-to-end`,
      RESUME_OPTIONS: (id) => `/executions/${id}/resume-options`,
      RESUME_CHECKPOINT: (id) => `/executions/${id}/resume-from-checkpoint`,
      CONTINUE_CHECKPOINT: (id) => `/executions/${id}/continue-checkpoint`,
      BYPASS_CHECKPOINT: (id) => `/executions/${id}/bypass-checkpoint`
    },
    DEBUG: {
      RERUN: (id) => `/debug/rerun/${id}`
    }
  }
}))

vi.mock('@/api/normalizers/executionStatus', () => ({
  normalizeExecutionStatus: vi.fn((data) => ({
    ok: data.ok !== false,
    status: data.status || 'unknown',
    ...data
  }))
}))

import { get, post } from '@/api/client'
import {
  getExecutionStatus,
  cancelExecution,
  pauseExecution,
  resumeExecution,
  stepExecution,
  runToEnd,
  getExecutionState,
  getResumeOptions,
  resumeFromCheckpoint,
  continueFromCheckpoint,
  bypassCheckpoint,
  rerunFromNode
} from '@/api/executions'

describe('Executions API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // getExecutionStatus
  // =========================================================================

  describe('getExecutionStatus()', () => {
    it('calls GET /executions/:id and normalizes response', async () => {
      get.mockResolvedValue({ ok: true, status: 'running', progress: 50 })

      const result = await getExecutionStatus('exec-1')

      expect(get).toHaveBeenCalledWith('/executions/exec-1')
      expect(result.ok).toBe(true)
      expect(result.status).toBe('running')
    })

    it('returns normalized error on failure', async () => {
      get.mockRejectedValue({ userMessage: 'Not found', message: 'Not found' })

      const result = await getExecutionStatus('bad-id')

      expect(result.ok).toBe(false)
    })
  })

  // =========================================================================
  // cancelExecution
  // =========================================================================

  describe('cancelExecution()', () => {
    it('calls POST /executions/:id/cancel', async () => {
      post.mockResolvedValue({ ok: true, message: 'Cancelled' })

      const result = await cancelExecution('exec-1')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/cancel')
      expect(result.ok).toBe(true)
    })

    it('returns error object on failure', async () => {
      post.mockRejectedValue({ userMessage: 'Cannot cancel' })

      const result = await cancelExecution('exec-1')

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Cannot cancel')
    })
  })

  // =========================================================================
  // pauseExecution
  // =========================================================================

  describe('pauseExecution()', () => {
    it('calls POST /executions/:id/pause with reason', async () => {
      post.mockResolvedValue({ ok: true })

      await pauseExecution('exec-1', 'breakpoint')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/pause', { reason: 'breakpoint' })
    })

    it('defaults reason to user_request', async () => {
      post.mockResolvedValue({ ok: true })

      await pauseExecution('exec-1')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/pause', { reason: 'user_request' })
    })
  })

  // =========================================================================
  // resumeExecution
  // =========================================================================

  describe('resumeExecution()', () => {
    it('calls POST /executions/:id/resume', async () => {
      post.mockResolvedValue({ ok: true })

      await resumeExecution('exec-1')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/resume')
    })
  })

  // =========================================================================
  // stepExecution
  // =========================================================================

  describe('stepExecution()', () => {
    it('calls POST /executions/:id/step', async () => {
      post.mockResolvedValue({ ok: true })

      await stepExecution('exec-1')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/step')
    })
  })

  // =========================================================================
  // runToEnd
  // =========================================================================

  describe('runToEnd()', () => {
    it('calls POST /executions/:id/run-to-end', async () => {
      post.mockResolvedValue({ ok: true })

      await runToEnd('exec-1')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/run-to-end')
    })
  })

  // =========================================================================
  // getExecutionState
  // =========================================================================

  describe('getExecutionState()', () => {
    it('calls GET /executions/:id/state', async () => {
      get.mockResolvedValue({ ok: true, state: { variables: {} } })

      const result = await getExecutionState('exec-1')

      expect(get).toHaveBeenCalledWith('/executions/exec-1/state')
      expect(result.ok).toBe(true)
    })
  })

  // =========================================================================
  // getResumeOptions
  // =========================================================================

  describe('getResumeOptions()', () => {
    it('calls GET /executions/:id/resume-options', async () => {
      get.mockResolvedValue({ ok: true, options: { checkpoints: [] } })

      const result = await getResumeOptions('exec-1')

      expect(get).toHaveBeenCalledWith('/executions/exec-1/resume-options')
      expect(result.ok).toBe(true)
    })
  })

  // =========================================================================
  // resumeFromCheckpoint
  // =========================================================================

  describe('resumeFromCheckpoint()', () => {
    it('calls POST /executions/:id/resume-from-checkpoint with checkpointId', async () => {
      post.mockResolvedValue({ ok: true, newExecutionId: 'exec-2' })

      const result = await resumeFromCheckpoint('exec-1', 'cp-1')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/resume-from-checkpoint', {
        checkpointId: 'cp-1',
        modifiedVariables: null
      })
      expect(result.newExecutionId).toBe('exec-2')
    })

    it('passes modifiedVariables when provided', async () => {
      post.mockResolvedValue({ ok: true })

      await resumeFromCheckpoint('exec-1', 'cp-1', { url: 'https://new.com' })

      expect(post).toHaveBeenCalledWith('/executions/exec-1/resume-from-checkpoint', {
        checkpointId: 'cp-1',
        modifiedVariables: { url: 'https://new.com' }
      })
    })
  })

  // =========================================================================
  // continueFromCheckpoint
  // =========================================================================

  describe('continueFromCheckpoint()', () => {
    it('calls POST /executions/:id/continue-checkpoint', async () => {
      post.mockResolvedValue({ ok: true })

      const result = await continueFromCheckpoint('exec-1')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/continue-checkpoint')
      expect(result.ok).toBe(true)
    })
  })

  // =========================================================================
  // bypassCheckpoint
  // =========================================================================

  describe('bypassCheckpoint()', () => {
    it('calls POST /executions/:id/bypass-checkpoint with default scope', async () => {
      post.mockResolvedValue({ ok: true })

      await bypassCheckpoint('exec-1', 'cp-1')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/bypass-checkpoint', {
        checkpointId: 'cp-1',
        scope: 'this_run'
      })
    })

    it('passes custom scope', async () => {
      post.mockResolvedValue({ ok: true })

      await bypassCheckpoint('exec-1', 'cp-1', 'this_version')

      expect(post).toHaveBeenCalledWith('/executions/exec-1/bypass-checkpoint', {
        checkpointId: 'cp-1',
        scope: 'this_version'
      })
    })
  })

  // =========================================================================
  // rerunFromNode
  // =========================================================================

  describe('rerunFromNode()', () => {
    it('calls POST /debug/rerun/:id with node_id and mode', async () => {
      post.mockResolvedValue({ success: true, new_execution_id: 'exec-new' })

      const result = await rerunFromNode('exec-1', 'node_abc')

      expect(post).toHaveBeenCalledWith('/debug/rerun/exec-1', {
        node_id: 'node_abc',
        mode: 'rehydrate',
        override_inputs: null
      })
      expect(result.ok).toBe(true)
      expect(result.newExecutionId).toBe('exec-new')
    })

    it('passes custom mode and overrideInputs', async () => {
      post.mockResolvedValue({ success: true, newExecutionId: 'exec-new' })

      await rerunFromNode('exec-1', 'node_abc', 'recompute', { url: 'test' })

      expect(post).toHaveBeenCalledWith('/debug/rerun/exec-1', {
        node_id: 'node_abc',
        mode: 'recompute',
        override_inputs: { url: 'test' }
      })
    })

    it('returns error on failure', async () => {
      post.mockRejectedValue({ userMessage: 'Execution not found' })

      const result = await rerunFromNode('bad', 'node')

      expect(result.ok).toBe(false)
      expect(result.error).toBe('Execution not found')
    })
  })
})
