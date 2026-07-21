import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBuilderWorkflowStore } from '@/stores/builder/workflowStore'

describe('useBuilderWorkflowStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useBuilderWorkflowStore()
  })

  // ==========================================================================
  // Initial State
  // ==========================================================================
  describe('initial state', () => {
    it('has correct defaults', () => {
      expect(store.nodes).toEqual([])
      expect(store.edges).toEqual([])
      expect(store.selectedNodeId).toBeNull()
      expect(store.viewport).toBeNull()
      expect(store.checkpoints).toEqual([])
    })
  })

  // ==========================================================================
  // Getters
  // ==========================================================================
  describe('getters', () => {
    it('elements combines nodes and edges', () => {
      store.nodes = [{ id: 'n1', data: {} }]
      store.edges = [{ id: 'e1', source: 'n1', target: 'n2' }]

      expect(store.elements).toHaveLength(2)
    })

    it('selectedNode returns the selected node', () => {
      store.nodes = [
        { id: 'n1', data: { module: 'a' } },
        { id: 'n2', data: { module: 'b' } }
      ]
      store.selectedNodeId = 'n2'

      expect(store.selectedNode).toEqual({ id: 'n2', data: { module: 'b' } })
    })

    it('selectedNode returns null when no selection', () => {
      expect(store.selectedNode).toBeNull()
    })

    it('hasCheckpoints returns false when empty', () => {
      expect(store.hasCheckpoints).toBe(false)
    })

    it('hasCheckpoints returns true when checkpoints exist', () => {
      store.checkpoints = ['n1']
      expect(store.hasCheckpoints).toBe(true)
    })

    it('hasCheckpoint checks specific node', () => {
      store.checkpoints = ['n1', 'n2']
      expect(store.hasCheckpoint('n1')).toBe(true)
      expect(store.hasCheckpoint('n3')).toBe(false)
    })
  })

  // ==========================================================================
  // Node Actions
  // ==========================================================================
  describe('setElements', () => {
    it('separates nodes and edges', () => {
      store.setElements([
        { id: 'n1', data: {} },
        { id: 'n2', data: {} },
        { id: 'e1', source: 'n1', target: 'n2' }
      ])

      expect(store.nodes).toHaveLength(2)
      expect(store.edges).toHaveLength(1)
    })

    it('handles null and mixed element payloads safely', () => {
      expect(store.setElements(null)).toBe(true)
      expect(store.nodes).toEqual([])
      expect(store.edges).toEqual([])

      store.setElements([
        null,
        'bad',
        { id: 'n1', data: {} },
        { id: 'e1', source: 'n1', target: 'n2' },
        { bad: true }
      ])

      expect(store.nodes).toEqual([{ id: 'n1', data: {} }])
      expect(store.edges).toEqual([{ id: 'e1', source: 'n1', target: 'n2' }])
    })
  })

  describe('addNode', () => {
    it('adds a node to the list', () => {
      store.addNode({ id: 'n1', data: { module: 'test' } })

      expect(store.nodes).toHaveLength(1)
      expect(store.nodes[0].id).toBe('n1')
    })

    it('rejects invalid node payloads without throwing', () => {
      expect(store.addNode(null)).toBe(false)
      expect(store.addNode({ data: {} })).toBe(false)
      expect(store.nodes).toEqual([])
    })
  })

  describe('createNodeFromModule', () => {
    it('creates node with module id and default params', () => {
      const module = { module: 'browser.open', params: { url: '' } }

      const node = store.createNodeFromModule(module, { id: 'node-test' })

      expect(node.id).toBe('node-test')
      expect(node.type).toBe('custom')
      expect(node.data.module).toBe('browser.open')
      expect(node.data.params).toEqual({ url: '' })
      expect(store.nodes).toContainEqual(node)
    })

    it('uses moduleId as fallback', () => {
      const module = { moduleId: 'data.extract', defaultParams: { selector: '' } }

      const node = store.createNodeFromModule(module, { id: 'n-x' })

      expect(node.data.module).toBe('data.extract')
      expect(node.data.params).toEqual({ selector: '' })
    })

    it('uses default position when not specified', () => {
      const node = store.createNodeFromModule({ module: 'test' })

      expect(node.position).toEqual({ x: 250, y: 150 })
    })

    it('uses custom position when provided', () => {
      const node = store.createNodeFromModule(
        { module: 'test' },
        { position: { x: 500, y: 300 } }
      )

      expect(node.position).toEqual({ x: 500, y: 300 })
    })

    it('creates a safe placeholder when module metadata is missing', () => {
      const node = store.createNodeFromModule(null, { id: 'missing-module', position: null })

      expect(node.id).toBe('missing-module')
      expect(node.data.module).toBe('unknown')
      expect(node.data.params).toEqual({})
      expect(node.position).toEqual({ x: 250, y: 150 })
    })

    it('deep clones params to avoid mutation', () => {
      const originalParams = { nested: { value: 'original' } }
      const module = { module: 'test', params: originalParams }

      const node = store.createNodeFromModule(module)

      node.data.params.nested.value = 'changed'
      expect(originalParams.nested.value).toBe('original')
    })
  })

  describe('updateNode', () => {
    it('updates node data', () => {
      store.nodes = [{ id: 'n1', data: { module: 'old', params: {} } }]

      const result = store.updateNode('n1', { params: { url: 'new' } })

      expect(result).toBe(true)
      expect(store.nodes[0].data.params).toEqual({ url: 'new' })
    })

    it('returns false for nonexistent node', () => {
      const result = store.updateNode('nonexistent', { params: {} })
      expect(result).toBe(false)
    })
  })

  describe('deleteNode', () => {
    it('removes node and connected edges', () => {
      store.nodes = [
        { id: 'n1', data: {} },
        { id: 'n2', data: {} },
        { id: 'n3', data: {} }
      ]
      store.edges = [
        { id: 'e1', source: 'n1', target: 'n2' },
        { id: 'e2', source: 'n2', target: 'n3' }
      ]

      store.deleteNode('n2')

      expect(store.nodes).toHaveLength(2)
      expect(store.nodes.find(n => n.id === 'n2')).toBeUndefined()
      expect(store.edges).toHaveLength(0)
    })

    it('clears selection if deleted node was selected', () => {
      store.nodes = [{ id: 'n1', data: {} }]
      store.selectedNodeId = 'n1'

      store.deleteNode('n1')

      expect(store.selectedNodeId).toBeNull()
    })

    it('removes checkpoint for deleted node', () => {
      store.nodes = [{ id: 'n1', data: {} }]
      store.checkpoints = ['n1']

      store.deleteNode('n1')

      expect(store.checkpoints).toEqual([])
    })
  })

  describe('selectNode / clearNodeSelection', () => {
    it('selects a node', () => {
      store.selectNode('n1')
      expect(store.selectedNodeId).toBe('n1')
    })

    it('clears selection', () => {
      store.selectedNodeId = 'n1'
      store.clearNodeSelection()
      expect(store.selectedNodeId).toBeNull()
    })
  })

  // ==========================================================================
  // Edge Actions
  // ==========================================================================
  describe('addEdge', () => {
    it('adds an edge', () => {
      store.addEdge({ id: 'e1', source: 'n1', target: 'n2' })

      expect(store.edges).toHaveLength(1)
    })

    it('rejects invalid edge payloads without throwing', () => {
      expect(store.addEdge(null)).toBe(false)
      expect(store.addEdge({ id: 'e1', source: 'n1' })).toBe(false)
      expect(store.edges).toEqual([])
    })
  })

  describe('deleteEdge', () => {
    it('removes edge by id', () => {
      store.edges = [
        { id: 'e1', source: 'n1', target: 'n2' },
        { id: 'e2', source: 'n2', target: 'n3' }
      ]

      store.deleteEdge('e1')

      expect(store.edges).toHaveLength(1)
      expect(store.edges[0].id).toBe('e2')
    })
  })

  // ==========================================================================
  // Checkpoint Actions
  // ==========================================================================
  describe('toggleCheckpoint', () => {
    it('adds checkpoint when not present', () => {
      store.toggleCheckpoint('n1')
      expect(store.checkpoints).toContain('n1')
    })

    it('removes checkpoint when already present', () => {
      store.checkpoints = ['n1']
      store.toggleCheckpoint('n1')
      expect(store.checkpoints).not.toContain('n1')
    })
  })

  describe('addCheckpoint', () => {
    it('adds new checkpoint', () => {
      expect(store.addCheckpoint('n1')).toBe(true)
      expect(store.checkpoints).toContain('n1')
    })

    it('does not duplicate', () => {
      store.checkpoints = ['n1']
      expect(store.addCheckpoint('n1')).toBe(false)
      expect(store.checkpoints).toHaveLength(1)
    })
  })

  describe('removeCheckpoint', () => {
    it('removes existing checkpoint', () => {
      store.checkpoints = ['n1', 'n2']
      expect(store.removeCheckpoint('n1')).toBe(true)
      expect(store.checkpoints).toEqual(['n2'])
    })

    it('returns false when not found', () => {
      expect(store.removeCheckpoint('nonexistent')).toBe(false)
    })
  })

  describe('clearCheckpoints', () => {
    it('removes all checkpoints', () => {
      store.checkpoints = ['n1', 'n2', 'n3']
      store.clearCheckpoints()
      expect(store.checkpoints).toEqual([])
    })
  })

  // ==========================================================================
  // Viewport
  // ==========================================================================
  describe('setViewport', () => {
    it('stores viewport', () => {
      store.setViewport({ x: 100, y: 200, zoom: 1.5 })
      expect(store.viewport).toEqual({ x: 100, y: 200, zoom: 1.5 })
    })
  })

  // ==========================================================================
  // Reset
  // ==========================================================================
  describe('reset', () => {
    it('resets all state', () => {
      store.nodes = [{ id: 'n1', data: {} }]
      store.edges = [{ id: 'e1', source: 'n1', target: 'n2' }]
      store.selectedNodeId = 'n1'
      store.viewport = { x: 0, y: 0, zoom: 1 }
      store.checkpoints = ['n1']

      store.reset()

      expect(store.nodes).toEqual([])
      expect(store.edges).toEqual([])
      expect(store.selectedNodeId).toBeNull()
      expect(store.viewport).toBeNull()
      expect(store.checkpoints).toEqual([])
    })
  })
})
