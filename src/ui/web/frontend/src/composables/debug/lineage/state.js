/**
 * Lineage State Factory
 *
 * S-Grade: State creation for lineage composable.
 * Single responsibility: State and computed definitions.
 */

import { ref, computed } from 'vue'

/**
 * Create initial state for lineage
 * @returns {Object} State refs
 */
export function createLineageState() {
  // View mode: 'lineage' (swimlane) or 'execution' (full graph)
  const viewMode = ref('lineage')

  // Swimlane view data
  const swimlane = ref({
    sources: [],
    transforms: [],
    sinks: [],
    dataEdges: [],
    stateNodes: [],
    groups: []
  })

  // Execution view data (full graph)
  const graph = ref({ nodes: [], edges: [] })

  // Focus mode state
  const focusedNode = ref(null)
  const focusData = ref(null)

  // Selected node for detail panel
  const selectedNode = ref(null)
  const dependencies = ref([])

  // Loading and error state
  const isLoading = ref(false)
  const error = ref(null)

  // Highlighted path (for variable tracing)
  const highlightedPath = ref([])

  // Item-level lineage state
  const itemLineage = ref({
    trackedOutputs: [],
    totalItemsTracked: 0
  })
  const selectedItemOrigins = ref(null)

  return {
    viewMode,
    swimlane,
    graph,
    focusedNode,
    focusData,
    selectedNode,
    dependencies,
    isLoading,
    error,
    highlightedPath,
    itemLineage,
    selectedItemOrigins
  }
}

/**
 * Create computed properties for lineage
 * @param {Object} state - State refs
 * @returns {Object} Computed properties
 */
export function createLineageComputed(state) {
  const { viewMode, swimlane, graph, focusedNode, focusData } = state

  const nodeCount = computed(() => {
    if (viewMode.value === 'lineage') {
      return swimlane.value.sources.length +
             swimlane.value.transforms.length +
             swimlane.value.sinks.length
    }
    return graph.value.nodes.length
  })

  const edgeCount = computed(() => {
    if (viewMode.value === 'lineage') {
      return swimlane.value.dataEdges.length
    }
    return graph.value.edges.length
  })

  const hasData = computed(() => nodeCount.value > 0)

  // Get all nodes for current view
  const allNodes = computed(() => {
    if (viewMode.value === 'lineage') {
      return [
        ...swimlane.value.sources,
        ...swimlane.value.transforms,
        ...swimlane.value.sinks
      ]
    }
    return graph.value.nodes
  })

  // Get all edges for current view
  const allEdges = computed(() => {
    if (viewMode.value === 'lineage') {
      return swimlane.value.dataEdges
    }
    return graph.value.edges
  })

  // Nodes visible based on focus mode
  const visibleNodes = computed(() => {
    if (!focusedNode.value || !focusData.value) {
      return allNodes.value
    }

    const focusIds = new Set([
      focusedNode.value,
      ...(focusData.value.upstream || []).map(id => `step_${id}`),
      ...(focusData.value.downstream || []).map(id => `step_${id}`)
    ])

    return allNodes.value.filter(n => focusIds.has(n.id))
  })

  // Edges visible based on focus mode
  const visibleEdges = computed(() => {
    if (!focusedNode.value || !focusData.value) {
      return allEdges.value
    }

    const highlightEdges = focusData.value.highlight_edges || []
    const edgeSet = new Set(highlightEdges.map(e => `${e.source}-${e.target}`))

    return allEdges.value.filter(e => edgeSet.has(`${e.source}-${e.target}`))
  })

  return {
    nodeCount,
    edgeCount,
    hasData,
    allNodes,
    allEdges,
    visibleNodes,
    visibleEdges
  }
}

/**
 * Get empty swimlane structure
 */
export function getEmptySwimlane() {
  return {
    sources: [],
    transforms: [],
    sinks: [],
    dataEdges: [],
    stateNodes: [],
    groups: []
  }
}
