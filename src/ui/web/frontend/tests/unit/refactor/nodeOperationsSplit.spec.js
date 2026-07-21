/**
 * Refactor Validation: useNodeOperations Split
 *
 * Verifies that sub-modules export the correct shapes and
 * pure functions produce expected results.
 * No mocks — direct imports.
 */
import { describe, it, expect } from 'vitest'
import { hasPathBetween, createDeletionState } from '@/composables/workflowEditor/deletionState'
import { createModuleFiltering } from '@/composables/workflowEditor/moduleFiltering'
import { createMenuState } from '@/composables/workflowEditor/menuState'
import {
  initializeParams,
  calculateEdgeMidpoint,
  calculateMultiOutputPosition,
  calculateStandalonePosition
} from '@/composables/workflowEditor/nodeHelpers'

describe('nodeHelpers exports', () => {
  it('nodeHelpers exports are functions', () => {
    expect(typeof initializeParams).toBe('function')
    expect(typeof calculateEdgeMidpoint).toBe('function')
    expect(typeof calculateMultiOutputPosition).toBe('function')
    expect(typeof calculateStandalonePosition).toBe('function')
  })

  it('calculateStandalonePosition returns default for empty nodes', () => {
    const result = calculateStandalonePosition({ value: [] })
    expect(result).toEqual({ x: 250, y: 150 })
  })

  it('calculateEdgeMidpoint computes midpoint', () => {
    const source = { position: { x: 0, y: 0 }, dimensions: { width: 200, height: 80 } }
    const target = { position: { x: 0, y: 200 }, dimensions: { width: 200 } }
    const result = calculateEdgeMidpoint(source, target)
    expect(result.x).toBeDefined()
    expect(result.y).toBeDefined()
    // midpoint Y should be between source bottom and target top
    expect(result.y).toBeGreaterThanOrEqual(80)
    expect(result.y).toBeLessThanOrEqual(200)
  })
})

describe('hasPathBetween', () => {
  it('returns false for disconnected nodes', () => {
    const edges = [{ id: 'e1', source: 'A', target: 'B' }]
    expect(hasPathBetween('C', 'D', edges)).toBe(false)
  })

  it('returns true for connected nodes', () => {
    const edges = [
      { id: 'e1', source: 'A', target: 'B' },
      { id: 'e2', source: 'B', target: 'C' }
    ]
    expect(hasPathBetween('A', 'C', edges)).toBe(true)
  })

  it('returns false when only edge is excluded', () => {
    const edges = [{ id: 'e1', source: 'A', target: 'B' }]
    expect(hasPathBetween('A', 'B', edges, 'e1')).toBe(false)
  })
})

describe('createModuleFiltering', () => {
  it('returns expected shape', () => {
    const result = createModuleFiltering()
    expect(result).toHaveProperty('isLoadingCompatible')
    expect(result).toHaveProperty('filterModules')
    expect(typeof result.filterModules).toBe('function')
  })
})

describe('createMenuState', () => {
  it('returns expected shape', () => {
    const nodes = { value: [] }
    const result = createMenuState(nodes)
    expect(result).toHaveProperty('menuOpen')
    expect(result).toHaveProperty('pendingSourceNode')
    expect(result).toHaveProperty('isInsertionMode')
    expect(result).toHaveProperty('isReplaceMode')
    expect(result).toHaveProperty('setPendingConnection')
    expect(typeof result.setPendingConnection).toBe('function')
  })
})

describe('createDeletionState', () => {
  it('returns expected shape', () => {
    const result = createDeletionState()
    expect(result).toHaveProperty('showReconnectDialog')
    expect(result).toHaveProperty('pendingDeleteNodeId')
    expect(result).toHaveProperty('reconnectDialogTitle')
    expect(result).toHaveProperty('reconnectDialogMessage')
  })
})
