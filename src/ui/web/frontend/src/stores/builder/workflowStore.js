/**
 * Builder Workflow Store
 * Manages nodes, edges, and workflow structure
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { asObject, cloneBoundaryValue, normalizeWorkflowElements } from '@/utils/dataBoundary'

export const useBuilderWorkflowStore = defineStore('builder-workflow', () => {
  // ========== Workflow Elements ==========
  const nodes = ref([])
  const edges = ref([])
  const selectedNodeId = ref(null)

  // ========== Canvas Viewport ==========
  const viewport = ref(null) // { x, y, zoom }

  // ========== Human Checkpoints ==========
  const checkpoints = ref([])

  // ========== Getters ==========
  const elements = computed(() => [...nodes.value, ...edges.value])

  const selectedNode = computed(() => {
    if (!selectedNodeId.value) return null
    return nodes.value.find(n => n.id === selectedNodeId.value)
  })

  const hasCheckpoints = computed(() => checkpoints.value.length > 0)

  function hasCheckpoint(nodeId) {
    return checkpoints.value.includes(nodeId)
  }

  // ========== Node Actions ==========
  function setElements(newElements) {
    const normalized = normalizeWorkflowElements(newElements)
    nodes.value = normalized.nodes
    edges.value = normalized.edges
    return true
  }

  function addNode(node) {
    const safeNode = asObject(node)
    if (!safeNode.id) return false
    nodes.value.push(safeNode)
    return true
  }

  /**
   * Create a workflow node from a module definition
   * This is the factory function for creating nodes - keeps node structure consistent
   *
   * @param {Object} module - Module definition from catalog
   * @param {Object} options - Optional overrides for position, etc.
   * @returns {Object} The created node
   */
  function createNodeFromModule(module, options = {}) {
    const safeModule = asObject(module)
    const safeOptions = asObject(options)
    // Use moduleId as fallback if module property is undefined
    const moduleId = safeModule.module || safeModule.moduleId || 'unknown'

    const nodeId = safeOptions.id || `node_${Date.now()}`
    const position = asObject(safeOptions.position)
    const safePosition = {
      x: Number.isFinite(position.x) ? position.x : 250,
      y: Number.isFinite(position.y) ? position.y : 150
    }
    const params = asObject(safeModule.params ?? safeModule.defaultParams)

    const newNode = {
      id: nodeId,
      type: 'custom',
      position: safePosition,
      data: {
        module: moduleId,
        params: cloneBoundaryValue(params, {})
      }
    }

    // Add node to store
    nodes.value.push(newNode)

    return newNode
  }

  function updateNode(nodeId, data) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      node.data = asObject(node.data)
      Object.assign(node.data, asObject(data))
      return true
    }
    return false
  }

  function deleteNode(nodeId) {
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
    if (selectedNodeId.value === nodeId) {
      selectedNodeId.value = null
    }
    // Also remove checkpoint if exists
    removeCheckpoint(nodeId)
    return true
  }

  function selectNode(nodeId) {
    selectedNodeId.value = nodeId
  }

  function clearNodeSelection() {
    selectedNodeId.value = null
  }

  // ========== Edge Actions ==========
  function addEdge(edge) {
    const safeEdge = asObject(edge)
    if (!safeEdge.source || !safeEdge.target) return false
    edges.value.push(safeEdge)
    return true
  }

  function deleteEdge(edgeId) {
    edges.value = edges.value.filter(e => e.id !== edgeId)
    return true
  }

  // ========== Checkpoint Actions ==========
  function toggleCheckpoint(nodeId) {
    const index = checkpoints.value.indexOf(nodeId)
    if (index !== -1) {
      checkpoints.value.splice(index, 1)
    } else {
      checkpoints.value.push(nodeId)
    }
    return true
  }

  function addCheckpoint(nodeId) {
    if (!checkpoints.value.includes(nodeId)) {
      checkpoints.value.push(nodeId)
      return true
    }
    return false
  }

  function removeCheckpoint(nodeId) {
    const index = checkpoints.value.indexOf(nodeId)
    if (index !== -1) {
      checkpoints.value.splice(index, 1)
      return true
    }
    return false
  }

  function clearCheckpoints() {
    checkpoints.value = []
    return true
  }

  // ========== Viewport Actions ==========
  function setViewport(newViewport) {
    viewport.value = newViewport
  }

  // ========== Reset ==========
  function reset() {
    nodes.value = []
    edges.value = []
    selectedNodeId.value = null
    viewport.value = null
    checkpoints.value = []
  }

  return {
    // Workflow Elements
    nodes,
    edges,
    selectedNodeId,

    // Canvas Viewport
    viewport,

    // Human Checkpoints
    checkpoints,

    // Getters
    elements,
    selectedNode,
    hasCheckpoints,
    hasCheckpoint,

    // Node Actions
    setElements,
    addNode,
    createNodeFromModule,
    updateNode,
    deleteNode,
    selectNode,
    clearNodeSelection,

    // Edge Actions
    addEdge,
    deleteEdge,

    // Checkpoint Actions
    toggleCheckpoint,
    addCheckpoint,
    removeCheckpoint,
    clearCheckpoints,

    // Viewport Actions
    setViewport,

    // Reset
    reset
  }
})
