import { describe, it, expect } from 'vitest'
import {
  canAddResourceToHandle,
  getResourceSlotCounts,
  getResourceSlotState,
  getResourceSlotType
} from '@/composables/workflowEditor/nodeRules/resourceSlots'

describe('AI agent resource slot rules', () => {
  const edges = [
    { id: 'model', source: 'model1', target: 'agent1', targetHandle: 'target-model', data: { edgeType: 'resource' } },
    { id: 'memory', source: 'memory1', target: 'agent1', target_handle: 'target-memory', data: { edge_type: 'resource' } },
    { id: 'tool1', source: 'tool1', target: 'agent1', targetHandle: 'target-tools', data: { edgeType: 'resource' } },
    { id: 'tool2', source: 'tool2', target: 'agent1', targetHandle: 'target-tools', data: { edgeType: 'resource' } },
    { id: 'other', source: 'tool3', target: 'agent2', targetHandle: 'target-tools', data: { edgeType: 'resource' } }
  ]

  it('classifies known resource handles', () => {
    expect(getResourceSlotType('target-model')).toBe('model')
    expect(getResourceSlotType('target-memory')).toBe('memory')
    expect(getResourceSlotType('target-tools')).toBe('tools')
    expect(getResourceSlotType('target')).toBeNull()
  })

  it('counts resource edges for a single agent node', () => {
    expect(getResourceSlotCounts('agent1', edges)).toEqual({
      model: 1,
      memory: 1,
      tools: 2
    })
  })

  it('locks single-resource model and memory slots but not tools', () => {
    const state = getResourceSlotState('agent1', edges)

    expect(state.model.locked).toBe(true)
    expect(state.memory.locked).toBe(true)
    expect(state.tools.locked).toBe(false)
    expect(state.tools.count).toBe(2)
  })

  it('allows adding more tools while blocking duplicate model and memory', () => {
    expect(canAddResourceToHandle('agent1', 'target-model', edges)).toBe(false)
    expect(canAddResourceToHandle('agent1', 'target-memory', edges)).toBe(false)
    expect(canAddResourceToHandle('agent1', 'target-tools', edges)).toBe(true)
  })
})
