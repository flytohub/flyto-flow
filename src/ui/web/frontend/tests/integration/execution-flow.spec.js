/**
 * Integration Test: Execution Flow
 *
 * Tests the REAL execution data flow through multiple layers:
 * executionControlStore -> nodeOutputStore -> execution API
 *
 * Only HTTP boundary is mocked (API module). All store logic,
 * computed properties, and reactive updates are real.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'

// Mock only the HTTP boundary — the API module
vi.mock('@/api/executions', () => ({
  pauseExecution: vi.fn(),
  resumeExecution: vi.fn(),
  stepExecution: vi.fn(),
  getExecutionState: vi.fn(),
  getResumeOptions: vi.fn(),
  resumeFromCheckpoint: vi.fn(),
  continueFromCheckpoint: vi.fn(),
  bypassCheckpoint: vi.fn(),
  default: {}
}))

// Mock telemetry (side-effect only, not business logic)
vi.mock('@/services/telemetry', () => ({
  telemetry: { track: vi.fn() }
}))

import { useExecutionControlStore, useNodeOutputStore } from '@/stores/execution'
import * as executionAPI from '@/api/executions'

describe('Execution Flow Integration', () => {
  let execStore
  let nodeOutputStore

  beforeEach(() => {
    setActivePinia(createPinia())
    execStore = useExecutionControlStore()
    nodeOutputStore = useNodeOutputStore()
    vi.clearAllMocks()
  })

  // =========================================================================
  // Full Lifecycle: start -> poll -> update nodes -> complete
  // =========================================================================

  describe('full execution lifecycle', () => {
    it('should flow: setExecution -> fetchState -> node outputs update', async () => {
      // Step 1: Start execution
      execStore.setExecution('exec-001', 'running')

      expect(execStore.executionId).toBe('exec-001')
      expect(execStore.status).toBe('running')
      expect(execStore.isRunning).toBe(true)
      expect(execStore.canPause).toBe(true)
      expect(execStore.canResume).toBe(false)

      // Step 2: Mock a realistic state response and fetch
      executionAPI.getExecutionState.mockResolvedValueOnce({
        ok: true,
        currentNode: 'node-2',
        progress: 0.5,
        variables: {
          'node-1': {
            output: { text: 'Hello World', count: 42 },
            status: 'completed'
          },
          'node-2': 'raw-value-from-engine'
        },
        nodeOutputs: {
          'node-3': { screenshot: 'base64data' }
        }
      })

      await execStore.fetchState()

      // Verify real state was stored
      expect(execStore.currentState).not.toBeNull()
      expect(execStore.currentState.currentNode).toBe('node-2')
      expect(execStore.currentState.progress).toBe(0.5)

      // Verify node outputs were populated through real updateFromState
      const node1Output = nodeOutputStore.getNodeOutput('node-1')
      expect(node1Output).toEqual({ text: 'Hello World', count: 42 })

      // Verify raw value was wrapped correctly
      const node2Output = nodeOutputStore.getNodeOutput('node-2')
      expect(node2Output).toBe('raw-value-from-engine')

      // Verify nodeOutputs field was also processed
      const node3Output = nodeOutputStore.getNodeOutput('node-3')
      expect(node3Output).toEqual({ screenshot: 'base64data' })

      // Verify hasOutput works
      expect(nodeOutputStore.hasOutput('node-1')).toBe(true)
      expect(nodeOutputStore.hasOutput('nonexistent')).toBe(false)
    })

    it('should handle pause -> step -> resume lifecycle', async () => {
      execStore.setExecution('exec-002', 'running')

      // Pause
      executionAPI.pauseExecution.mockResolvedValueOnce({ ok: true })
      executionAPI.getExecutionState.mockResolvedValueOnce({
        ok: true,
        variables: {}
      })
      const paused = await execStore.pause('user_request')

      expect(paused).toBe(true)
      expect(execStore.status).toBe('paused')
      expect(execStore.isPaused).toBe(true)
      expect(execStore.canStep).toBe(true)
      expect(execStore.canResume).toBe(true)

      // Step
      executionAPI.stepExecution.mockResolvedValueOnce({ ok: true })
      executionAPI.getExecutionState.mockResolvedValueOnce({
        ok: true,
        variables: {
          'step-node': {
            output: { result: 'step-result' },
            status: 'completed'
          }
        }
      })
      const stepped = await execStore.step()

      expect(stepped).toBe(true)
      expect(execStore.status).toBe('paused') // back to paused after step
      expect(nodeOutputStore.getNodeOutput('step-node')).toEqual({ result: 'step-result' })

      // Resume
      executionAPI.resumeExecution.mockResolvedValueOnce({ ok: true })
      const resumed = await execStore.resume()

      expect(resumed).toBe(true)
      expect(execStore.status).toBe('running')
      expect(execStore.isRunning).toBe(true)
    })
  })

  // =========================================================================
  // Error Recovery
  // =========================================================================

  describe('error handling and recovery', () => {
    it('should propagate API errors to store error state', async () => {
      execStore.setExecution('exec-003', 'running')

      executionAPI.pauseExecution.mockRejectedValueOnce(
        new Error('Network timeout')
      )

      const result = await execStore.pause()
      expect(result).toBe(false)
      expect(execStore.error).toBe('Network timeout')
      expect(execStore.loading).toBe(false)
    })

    it('should prefer userMessage over generic message', async () => {
      execStore.setExecution('exec-004', 'running')

      const apiError = new Error('generic error')
      apiError.userMessage = 'Execution is no longer running'
      executionAPI.pauseExecution.mockRejectedValueOnce(apiError)

      await execStore.pause()
      expect(execStore.error).toBe('Execution is no longer running')
    })

    it('should handle fetchState error gracefully', async () => {
      execStore.setExecution('exec-005', 'running')

      executionAPI.getExecutionState.mockRejectedValueOnce(
        new Error('Server error')
      )

      const result = await execStore.fetchState()
      expect(result).toBeNull()
      expect(execStore.error).toBe('Server error')
      // State should remain unchanged
      expect(execStore.currentState).toBeNull()
    })

    it('should clear error state', () => {
      execStore.setExecution('exec-006')
      execStore.error = 'some error'
      execStore.clearError()
      expect(execStore.error).toBeNull()
    })
  })

  // =========================================================================
  // Resume from Checkpoint
  // =========================================================================

  describe('resume from checkpoint', () => {
    it('should fetch resume options and populate store', async () => {
      execStore.setExecution('exec-007', 'paused')

      executionAPI.getResumeOptions.mockResolvedValueOnce({
        ok: true,
        options: {
          canResume: true,
          checkpoints: [
            { id: 'cp-1', nodeId: 'node-1', label: 'After login' },
            { id: 'cp-2', nodeId: 'node-3', label: 'After data fetch' }
          ],
          recommendedCheckpoint: 'cp-2',
          failureNode: 'node-4',
          failureMessage: 'Element not found'
        }
      })

      await execStore.fetchResumeOptions()

      // Verify real computed properties work
      expect(execStore.hasResumeOptions).toBe(true)
      expect(execStore.checkpoints).toHaveLength(2)
      expect(execStore.recommendedCheckpoint).toBe('cp-2')
      expect(execStore.failureInfo).toEqual({
        node: 'node-4',
        message: 'Element not found'
      })
    })

    it('should resume from checkpoint and get new execution ID', async () => {
      execStore.setExecution('exec-008', 'paused')
      execStore.resumeOptions = { canResume: true }

      executionAPI.resumeFromCheckpoint.mockResolvedValueOnce({
        ok: true,
        newExecutionId: 'exec-009'
      })

      const result = await execStore.resumeFromCheckpoint('cp-1', { url: 'https://new-url.com' })

      expect(result.ok).toBe(true)
      expect(execStore.executionId).toBe('exec-009')
      expect(execStore.status).toBe('running')
      expect(execStore.resumeOptions).toBeNull()
      expect(execStore.currentState).toBeNull()
    })
  })

  // =========================================================================
  // Node Output Store (direct)
  // =========================================================================

  describe('node output store data integrity', () => {
    it('should track duration, startedAt, inputs, and error fields', () => {
      nodeOutputStore.setNodeOutput('node-x', {
        output: { data: 'result' },
        status: 'completed',
        durationMs: 1500,
        startedAt: '2026-01-15T10:00:00Z',
        inputs: { url: 'https://example.com' },
        error: null
      })

      expect(nodeOutputStore.getNodeDuration('node-x')).toBe(1500)
      expect(nodeOutputStore.getNodeStartedAt('node-x')).toBe('2026-01-15T10:00:00Z')
      expect(nodeOutputStore.getNodeInputs('node-x')).toEqual({ url: 'https://example.com' })
      expect(nodeOutputStore.getNodeError('node-x')).toBeNull()
      expect(nodeOutputStore.getNodeOutputInfo('node-x')).toMatchObject({
        output: { data: 'result' },
        status: 'completed',
        durationMs: 1500
      })
    })

    it('should handle display outputs grouping', () => {
      nodeOutputStore.updateDisplayOutputsFromList([
        { stepId: 'node-1', type: 'screenshot', dataUri: 'data:image/png;base64,abc' },
        { stepId: 'node-1', type: 'text', content: 'Page loaded' },
        { stepId: 'node-2', type: 'screenshot', dataUri: 'data:image/png;base64,def' }
      ])

      const node1Displays = nodeOutputStore.getNodeDisplayOutputs('node-1')
      expect(node1Displays).toHaveLength(2)
      expect(node1Displays[0].type).toBe('screenshot')
      expect(node1Displays[1].type).toBe('text')

      const node2Displays = nodeOutputStore.getNodeDisplayOutputs('node-2')
      expect(node2Displays).toHaveLength(1)
    })

    it('should clear all outputs on reset', () => {
      nodeOutputStore.setNodeOutput('node-a', { output: 'test', status: 'completed' })
      nodeOutputStore.updateDisplayOutputsFromList([
        { stepId: 'node-a', type: 'text', content: 'hello' }
      ])

      nodeOutputStore.reset()

      expect(nodeOutputStore.nodeOutputs).toEqual({})
      expect(nodeOutputStore.getNodeOutput('node-a')).toBeNull()
      expect(nodeOutputStore.getNodeDisplayOutputs('node-a')).toEqual([])
    })
  })

  // =========================================================================
  // Guard conditions
  // =========================================================================

  describe('guard conditions prevent invalid transitions', () => {
    it('should not pause when not running', async () => {
      execStore.setExecution('exec-010', 'paused')
      const result = await execStore.pause()
      expect(result).toBe(false)
      expect(executionAPI.pauseExecution).not.toHaveBeenCalled()
    })

    it('should not resume when not paused', async () => {
      execStore.setExecution('exec-011', 'running')
      const result = await execStore.resume()
      expect(result).toBe(false)
      expect(executionAPI.resumeExecution).not.toHaveBeenCalled()
    })

    it('should not step when not paused', async () => {
      execStore.setExecution('exec-012', 'running')
      const result = await execStore.step()
      expect(result).toBe(false)
      expect(executionAPI.stepExecution).not.toHaveBeenCalled()
    })

    it('should not fetch state without executionId', async () => {
      const result = await execStore.fetchState()
      expect(result).toBeNull()
      expect(executionAPI.getExecutionState).not.toHaveBeenCalled()
    })
  })

  // =========================================================================
  // Full reset
  // =========================================================================

  describe('full reset clears everything', () => {
    it('should reset all state including child stores', () => {
      // Set up some state
      execStore.setExecution('exec-020', 'running')
      nodeOutputStore.setNodeOutput('node-1', { output: 'data', status: 'completed' })

      execStore.reset()

      expect(execStore.executionId).toBeNull()
      expect(execStore.status).toBe('idle')
      expect(execStore.currentState).toBeNull()
      expect(execStore.loading).toBe(false)
      expect(execStore.error).toBeNull()
      expect(nodeOutputStore.nodeOutputs).toEqual({})
    })
  })
})
