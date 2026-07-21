/**
 * Node CRUD Composable
 *
 * Handles node creation (standalone, forward-connected, sub-node, template),
 * node insertion on an edge, and node replacement.
 */

import { useModulesStore } from '@/stores/modulesStore'
import { useToast } from '@/composables/useToast'
import {
  createEdge,
  createNode,
  calculateNewNodePosition,
  isMultiOutputNode
} from './useCanvasOperations'
import { isLoopEdge, getEdgeColorForSourceHandle } from './workflowConstants'
import { validateInsertion } from '@/api/modules'
import { nodeService } from '@/services/nodeService'
import { canAddResourceToHandle, getResourceSlotType } from './nodeRules/resourceSlots'

import {
  initializeParams,
  calculateEdgeMidpoint,
  calculateMultiOutputPosition,
  calculateStandalonePosition
} from './nodeHelpers'

/**
 * @param {Object} options
 * @param {Ref<Array>} options.nodes - Nodes array
 * @param {Ref<Array>} options.edges - Edges array
 * @param {Array} options.caseColors - Switch case colors
 */
export function useNodeCrud({ nodes, edges, caseColors = [] }) {
  const modulesStore = useModulesStore()
  const toast = useToast()

  /**
   * Resolve source handle and edge style for case-aware connections
   */
  function resolveEdgeStyle(sourceHandle, caseId, caseColor, sourceNode) {
    const resolvedHandle = sourceHandle === 'source-cases' && caseId
      ? `source-case-${caseId}`
      : sourceHandle
    const color = caseColor ||
      getEdgeColorForSourceHandle(resolvedHandle, sourceNode, caseColors)
    return { resolvedHandle, edgeOptions: color ? { color } : {} }
  }

  /**
   * Create a standalone node at specified position (no connections)
   */
  function createStandaloneNode(newId, moduleId, module, position = null) {
    const nodePosition = position || calculateStandalonePosition(nodes)

    const newNode = createNode({
      id: newId,
      type: 'custom',
      position: nodePosition,
      data: {
        module: moduleId,
        params: initializeParams(moduleId, module)
      }
    })

    nodes.value = [...nodes.value, newNode]
    return newNode
  }

  /**
   * Create a template node (Template as Node feature)
   */
  function createTemplateNode(newId, template, pendingState) {
    const {
      sourceNodeId,
      sourceHandle,
      caseColor,
      caseId,
      pendingCase,
      position: pendingPosition
    } = pendingState

    // Deferred case creation for switch node
    if (pendingCase && sourceNodeId) {
      const srcNode = nodes.value.find(n => n.id === sourceNodeId)
      if (srcNode) {
        if (!srcNode.data.params) srcNode.data.params = {}
        if (!Array.isArray(srcNode.data.params.cases)) srcNode.data.params.cases = []
        srcNode.data.params.cases.push(pendingCase)
      }
    }

    let position = pendingPosition
    if (!position) {
      if (!sourceNodeId) {
        position = calculateStandalonePosition(nodes)
      } else {
        const parentNode = nodes.value.find(n => n.id === sourceNodeId)
        position = parentNode ? calculateNewNodePosition(parentNode) : { x: 250, y: 150 }
      }
    }

    const moduleId = template.moduleId
    const defaultParams = initializeParams(moduleId, template, {
      template_id: template.templateId,
      library_id: template.libraryId,
    })
    const nodeData = {
      module: template.moduleId,
      label: template.label,
      icon: template.icon || 'Package',
      color: template.color || '#8B5CF6',
      params: defaultParams
    }

    const newNode = createNode({
      id: newId,
      type: 'custom',
      position,
      label: template.label,
      data: nodeData
    })

    nodes.value = [...nodes.value, newNode]

    let newEdge = null
    if (sourceNodeId) {
      const { resolvedHandle, edgeOptions } = resolveEdgeStyle(
        sourceHandle, caseId, caseColor, nodes.value.find(n => n.id === sourceNodeId)
      )

      const sourceNode = nodes.value.find(n => n.id === sourceNodeId)
      newEdge = createEdge(sourceNodeId, newId, resolvedHandle, null, {
        ...edgeOptions,
        sourceNodeData: sourceNode?.data,
        data: caseId ? { caseId } : undefined
      })

      edges.value = [...edges.value, newEdge]
    }

    return { node: newNode, edge: newEdge }
  }

  /**
   * Create AI Agent sub-node (reverse connection: new node -> parent)
   */
  function createSubNode(parentNode, newId, moduleId, module, pendingState) {
    const { targetHandle, subNodeType } = pendingState
    if (!canAddResourceToHandle(parentNode.id, targetHandle, edges.value)) {
      const slotType = getResourceSlotType(targetHandle) || 'resource'
      toast.warning(`Only one ${slotType} resource can be attached to this agent`)
      return null
    }

    const edgesToHandle = edges.value.filter(e =>
      e.target === parentNode.id && e.targetHandle === targetHandle
    )
    const stackOffset = edgesToHandle.length * 100

    let position = { x: parentNode.position.x, y: parentNode.position.y + 180 }
    if (targetHandle === 'target-model') {
      position.x = parentNode.position.x - 100 + stackOffset
    } else if (targetHandle === 'target-memory') {
      position.x = parentNode.position.x + 60 + stackOffset
    } else if (targetHandle === 'target-tools') {
      position.x = parentNode.position.x + 220 + stackOffset
    }

    const newNode = createNode({
      id: newId,
      type: 'custom',
      position,
      data: {
        module: moduleId,
        params: initializeParams(moduleId, module),
        isSubNode: true,
        subNodeType: subNodeType
      }
    })

    const edgeColor = targetHandle === 'target-model' ? '#10B981' :
                      targetHandle === 'target-memory' ? '#8B5CF6' : '#F59E0B'
    const newEdge = createEdge(newId, parentNode.id, 'target', targetHandle, {
      color: edgeColor,
      type: 'smoothstep',
      edgeType: 'resource'
    })

    nodes.value = [...nodes.value, newNode]
    edges.value = [...edges.value, newEdge]

    return { node: newNode, edge: newEdge }
  }

  /**
   * Create normal forward-connected node
   */
  function createForwardNode(parentNode, newId, moduleId, module, pendingState) {
    const { sourceHandle, caseColor, caseId, pendingCase } = pendingState
    const parentModuleId = parentNode.data?.module || ''

    // Deferred case creation
    if (pendingCase) {
      if (!parentNode.data.params) parentNode.data.params = {}
      if (!Array.isArray(parentNode.data.params.cases)) parentNode.data.params.cases = []
      parentNode.data.params.cases.push(pendingCase)
    }

    const existingOutgoingEdges = edges.value.filter(
      e => e.source === parentNode.id && !isLoopEdge(e)
    )
    const sourceIsMultiOutput = isMultiOutputNode(parentModuleId, modulesStore)

    let position = calculateNewNodePosition(parentNode)

    if (sourceIsMultiOutput && sourceHandle) {
      position = calculateMultiOutputPosition(parentNode, sourceHandle, caseId, edges)
    }

    if (!sourceIsMultiOutput && existingOutgoingEdges.length > 0) {
      position = {
        x: position.x,
        y: position.y + (existingOutgoingEdges.length * 120)
      }
    }

    const { resolvedHandle, edgeOptions } = resolveEdgeStyle(sourceHandle, caseId, caseColor, parentNode)

    const newNode = createNode({
      id: newId,
      type: 'custom',
      position,
      data: {
        module: moduleId,
        params: initializeParams(moduleId, module)
      }
    })

    const resolvedTargetHandle = resolvedHandle === 'body_out' ? 'target-top' : null
    const newEdge = createEdge(parentNode.id, newId, resolvedHandle, resolvedTargetHandle, {
      ...edgeOptions,
      sourceNodeData: parentNode.data,
      data: caseId ? { caseId } : undefined
    })

    nodes.value = [...nodes.value, newNode]
    edges.value = [...edges.value, newEdge]

    return { node: newNode, edge: newEdge }
  }

  /**
   * Insert a node in the middle of an edge.
   * Splits the edge into two: source -> newNode -> target
   */
  async function insertNodeOnEdge(newId, moduleId, module, edge) {
    if (!edge) {
      return null
    }

    const sourceNode = nodes.value.find(n => n.id === edge.source)
    const targetNode = nodes.value.find(n => n.id === edge.target)

    if (!sourceNode || !targetNode) {
      return null
    }

    // 1. Calculate midpoint position
    const position = calculateEdgeMidpoint(sourceNode, targetNode)

    // 2. Create new node at midpoint
    const newNode = createNode({
      id: newId,
      type: 'custom',
      position,
      data: {
        module: moduleId,
        params: initializeParams(moduleId, module)
      }
    })

    // 3. Preserve edge data from original edge
    const originalEdgeData = edge.data || {}
    const originalSourceHandle = edge.sourceHandle || null
    const originalTargetHandle = edge.targetHandle || null
    const originalEdgeColor = edge.style?.stroke || edge.markerEnd?.color

    // 4. Infer handles from new node's metadata
    const newNodeInputHandles = nodeService.getInputHandles(moduleId, modulesStore)
    const newNodeOutputHandles = nodeService.getOutputHandles(moduleId, modulesStore)
    const newNodeFirstInput = newNodeInputHandles.length > 0 ? newNodeInputHandles[0].id : null
    const newNodeFirstOutput = newNodeOutputHandles.length > 0 ? newNodeOutputHandles[0].id : null

    // 5. Create two new edges
    const edge1Options = {}
    if (originalEdgeColor) edge1Options.color = originalEdgeColor
    if (originalEdgeData.caseId) edge1Options.data = { caseId: originalEdgeData.caseId }
    if (originalEdgeData.label) edge1Options.label = originalEdgeData.label

    const newEdge1 = createEdge(
      edge.source,
      newId,
      originalSourceHandle,
      newNodeFirstInput,
      edge1Options
    )

    const newEdge2 = createEdge(
      newId,
      edge.target,
      newNodeFirstOutput,
      originalTargetHandle
    )

    // 6. Save original state for undo
    const originalNodes = [...nodes.value]
    const originalEdges = [...edges.value]

    // 7. Remove original edge, add new node and edges
    const filteredEdges = edges.value.filter(e => e.id !== edge.id)
    nodes.value = [...nodes.value, newNode]
    edges.value = [...filteredEdges, newEdge1, newEdge2]

    // 8. Validate insertion with backend
    const sourceModuleId = sourceNode.data?.module
    const targetModuleId = targetNode.data?.module

    if (sourceModuleId && targetModuleId) {
      try {
        const result = await validateInsertion(
          sourceModuleId,
          moduleId,
          targetModuleId,
          originalSourceHandle || 'output',
          originalTargetHandle || 'input'
        )
        if (!result?.valid) {
          nodes.value = originalNodes
          edges.value = originalEdges
          const reason = result?.reason || 'Module is not compatible for insertion at this position'
          toast.warning(reason)
          return null
        }
      } catch (err) {
        nodes.value = originalNodes
        edges.value = originalEdges
        toast.warning('Failed to validate insertion')
        return null
      }
    }

    return {
      node: newNode,
      edges: [newEdge1, newEdge2],
      removedEdge: edge
    }
  }

  /**
   * Get upstream and downstream module IDs for a node
   */
  function getNodeConnections(nodeId) {
    const incomingEdges = edges.value.filter(e => e.target === nodeId)
    const outgoingEdges = edges.value.filter(e => e.source === nodeId && !isLoopEdge(e))

    let upstreamModuleId = null
    let downstreamModuleId = null

    if (incomingEdges.length > 0) {
      const sourceNode = nodes.value.find(n => n.id === incomingEdges[0].source)
      upstreamModuleId = sourceNode?.data?.module
    }

    if (outgoingEdges.length > 0) {
      const targetNode = nodes.value.find(n => n.id === outgoingEdges[0].target)
      downstreamModuleId = targetNode?.data?.module
    }

    return { upstreamModuleId, downstreamModuleId }
  }

  /**
   * Replace an existing node with a new module.
   * Keeps the same position and reconnects all edges.
   */
  function replaceNode(nodeId, moduleId, module) {
    const existingNode = nodes.value.find(n => n.id === nodeId)
    if (!existingNode) {
      return null
    }

    existingNode.data = {
      ...existingNode.data,
      module: moduleId,
      params: initializeParams(moduleId, module)
    }

    nodes.value = [...nodes.value]

    return existingNode
  }

  return {
    resolveEdgeStyle,
    createStandaloneNode,
    createTemplateNode,
    createSubNode,
    createForwardNode,
    insertNodeOnEdge,
    getNodeConnections,
    replaceNode
  }
}
