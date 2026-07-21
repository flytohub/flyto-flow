import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNodeOutputStore } from '@/stores/execution/nodeOutputStore'

describe('useNodeOutputStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useNodeOutputStore()
  })

  // ==========================================================================
  // Initial State
  // ==========================================================================
  describe('initial state', () => {
    it('has empty outputs', () => {
      expect(store.nodeOutputs).toEqual({})
      expect(store.nodeDisplayOutputs).toEqual({})
    })
  })

  // ==========================================================================
  // setNodeOutput
  // ==========================================================================
  describe('setNodeOutput', () => {
    it('stores output with metadata', () => {
      store.setNodeOutput('node-1', {
        output: { result: 'success' },
        status: 'completed',
        durationMs: 1500,
        startedAt: '2026-01-01T00:00:00Z',
        inputs: { url: 'https://example.com' },
        error: null
      })

      const stored = store.nodeOutputs['node-1']
      expect(stored.output).toEqual({ result: 'success' })
      expect(stored.status).toBe('completed')
      expect(stored.durationMs).toBe(1500)
      expect(stored.startedAt).toBe('2026-01-01T00:00:00Z')
      expect(stored.inputs).toEqual({ url: 'https://example.com' })
      expect(stored.error).toBeNull()
      expect(stored.fetchedAt).toBeGreaterThan(0)
    })

    it('defaults optional fields to null', () => {
      store.setNodeOutput('node-1', {
        output: 'data',
        status: 'completed'
      })

      const stored = store.nodeOutputs['node-1']
      expect(stored.durationMs).toBeNull()
      expect(stored.startedAt).toBeNull()
      expect(stored.inputs).toBeNull()
      expect(stored.error).toBeNull()
    })

    it('overwrites existing output', () => {
      store.setNodeOutput('node-1', { output: 'first', status: 'running' })
      store.setNodeOutput('node-1', { output: 'second', status: 'completed' })

      expect(store.nodeOutputs['node-1'].output).toBe('second')
      expect(store.nodeOutputs['node-1'].status).toBe('completed')
    })
  })

  // ==========================================================================
  // updateFromState
  // ==========================================================================
  describe('updateFromState', () => {
    it('handles structured format { output, status }', () => {
      store.updateFromState({
        'node-1': { output: 'data', status: 'completed' }
      })

      expect(store.getNodeOutput('node-1')).toBe('data')
    })

    it('wraps raw value format as completed', () => {
      store.updateFromState({
        'node-1': 'raw-value'
      })

      expect(store.getNodeOutput('node-1')).toBe('raw-value')
      expect(store.nodeOutputs['node-1'].status).toBe('completed')
    })

    it('wraps array values as completed', () => {
      store.updateFromState({
        'node-1': [1, 2, 3]
      })

      expect(store.getNodeOutput('node-1')).toEqual([1, 2, 3])
    })

    it('skips null/undefined values', () => {
      store.updateFromState({
        'node-1': null,
        'node-2': undefined,
        'node-3': 'valid'
      })

      expect(store.hasOutput('node-1')).toBe(false)
      expect(store.hasOutput('node-2')).toBe(false)
      expect(store.hasOutput('node-3')).toBe(true)
    })

    it('does nothing when variables is null', () => {
      store.updateFromState(null)
      expect(store.nodeOutputs).toEqual({})
    })

    it('does nothing when variables is undefined', () => {
      store.updateFromState(undefined)
      expect(store.nodeOutputs).toEqual({})
    })
  })

  // ==========================================================================
  // getNodeOutput
  // ==========================================================================
  describe('getNodeOutput', () => {
    it('returns output for existing node', () => {
      store.setNodeOutput('node-1', { output: 'data', status: 'completed' })
      expect(store.getNodeOutput('node-1')).toBe('data')
    })

    it('returns null for missing node', () => {
      expect(store.getNodeOutput('nonexistent')).toBeNull()
    })
  })

  // ==========================================================================
  // getNodeOutputInfo
  // ==========================================================================
  describe('getNodeOutputInfo', () => {
    it('returns full info for existing node', () => {
      store.setNodeOutput('node-1', { output: 'data', status: 'completed', durationMs: 100 })
      const info = store.getNodeOutputInfo('node-1')

      expect(info.output).toBe('data')
      expect(info.status).toBe('completed')
      expect(info.durationMs).toBe(100)
    })

    it('returns null for missing node', () => {
      expect(store.getNodeOutputInfo('missing')).toBeNull()
    })
  })

  // ==========================================================================
  // hasOutput
  // ==========================================================================
  describe('hasOutput', () => {
    it('returns true for existing node', () => {
      store.setNodeOutput('node-1', { output: 'data', status: 'completed' })
      expect(store.hasOutput('node-1')).toBe(true)
    })

    it('returns false for missing node', () => {
      expect(store.hasOutput('missing')).toBe(false)
    })
  })

  // ==========================================================================
  // Accessor functions
  // ==========================================================================
  describe('getNodeDuration', () => {
    it('returns duration for existing node', () => {
      store.setNodeOutput('node-1', { output: 'x', status: 'completed', durationMs: 2500 })
      expect(store.getNodeDuration('node-1')).toBe(2500)
    })

    it('returns null for missing node', () => {
      expect(store.getNodeDuration('missing')).toBeNull()
    })
  })

  describe('getNodeInputs', () => {
    it('returns inputs for existing node', () => {
      store.setNodeOutput('node-1', { output: 'x', status: 'ok', inputs: { url: 'test' } })
      expect(store.getNodeInputs('node-1')).toEqual({ url: 'test' })
    })

    it('returns null for missing node', () => {
      expect(store.getNodeInputs('missing')).toBeNull()
    })
  })

  describe('getNodeError', () => {
    it('returns error for existing node', () => {
      store.setNodeOutput('node-1', { output: null, status: 'failed', error: { message: 'Timeout' } })
      expect(store.getNodeError('node-1')).toEqual({ message: 'Timeout' })
    })

    it('returns null for node without error', () => {
      store.setNodeOutput('node-1', { output: 'ok', status: 'completed' })
      expect(store.getNodeError('node-1')).toBeNull()
    })
  })

  describe('getNodeStartedAt', () => {
    it('returns startedAt for existing node', () => {
      store.setNodeOutput('node-1', { output: 'x', status: 'ok', startedAt: '2026-01-01' })
      expect(store.getNodeStartedAt('node-1')).toBe('2026-01-01')
    })

    it('returns null for missing node', () => {
      expect(store.getNodeStartedAt('missing')).toBeNull()
    })
  })

  // ==========================================================================
  // Display Outputs
  // ==========================================================================
  describe('updateDisplayOutputsFromList', () => {
    it('groups display outputs by stepId', () => {
      store.updateDisplayOutputsFromList([
        { stepId: 'node-1', type: 'screenshot', content: 'img1' },
        { stepId: 'node-1', type: 'text', content: 'Hello' },
        { stepId: 'node-2', type: 'screenshot', content: 'img2' }
      ])

      expect(store.getNodeDisplayOutputs('node-1')).toHaveLength(2)
      expect(store.getNodeDisplayOutputs('node-2')).toHaveLength(1)
    })

    it('handles step_id (snake_case) format', () => {
      store.updateDisplayOutputsFromList([
        { step_id: 'node-1', type: 'text', content: 'Hello' }
      ])

      expect(store.getNodeDisplayOutputs('node-1')).toHaveLength(1)
    })

    it('skips items without stepId', () => {
      store.updateDisplayOutputsFromList([
        { type: 'text', content: 'no step id' },
        { stepId: 'node-1', type: 'text', content: 'ok' }
      ])

      expect(store.getNodeDisplayOutputs('node-1')).toHaveLength(1)
    })

    it('does nothing for empty array', () => {
      store.updateDisplayOutputsFromList([])
      expect(store.nodeDisplayOutputs).toEqual({})
    })

    it('does nothing for null', () => {
      store.updateDisplayOutputsFromList(null)
      expect(store.nodeDisplayOutputs).toEqual({})
    })
  })

  describe('getNodeDisplayOutputs', () => {
    it('returns empty array for missing node', () => {
      expect(store.getNodeDisplayOutputs('missing')).toEqual([])
    })
  })

  // ==========================================================================
  // Clear & Reset
  // ==========================================================================
  describe('clearNodeOutput', () => {
    it('removes specific node output', () => {
      store.setNodeOutput('node-1', { output: 'a', status: 'ok' })
      store.setNodeOutput('node-2', { output: 'b', status: 'ok' })

      store.clearNodeOutput('node-1')

      expect(store.hasOutput('node-1')).toBe(false)
      expect(store.hasOutput('node-2')).toBe(true)
    })
  })

  describe('clearAllOutputs', () => {
    it('clears all outputs and display outputs', () => {
      store.setNodeOutput('node-1', { output: 'a', status: 'ok' })
      store.updateDisplayOutputsFromList([{ stepId: 'node-1', type: 'text', content: 'x' }])

      store.clearAllOutputs()

      expect(store.nodeOutputs).toEqual({})
      expect(store.nodeDisplayOutputs).toEqual({})
    })
  })

  describe('reset', () => {
    it('resets all state', () => {
      store.setNodeOutput('node-1', { output: 'a', status: 'ok' })
      store.updateDisplayOutputsFromList([{ stepId: 'node-1', type: 'text', content: 'x' }])

      store.reset()

      expect(store.nodeOutputs).toEqual({})
      expect(store.nodeDisplayOutputs).toEqual({})
    })
  })
})
