/**
 * Previous Steps Composable
 * Provides upstream nodes for a given node in the workflow graph
 *
 * S-Grade Architecture: Graph traversal done on backend, frontend just looks up
 */

import { ref, computed, watch } from 'vue'
import { workflowAPI } from '@/api/workflows'

// Shared cache of graph relations (keyed by workflow structure hash)
const graphRelationsCache = ref({})
const lastComputeHash = ref(null)

/**
 * Computes a simple hash of elements to detect changes
 */
function computeElementsHash(elements) {
  if (!elements || !elements.length) return ''
  const nodeIds = elements
    .filter(el => el.id && !el.source)
    .map(n => n.id)
    .sort()
    .join(',')
  const edgeKeys = elements
    .filter(el => el.source && el.target)
    .map(e => `${e.source}->${e.target}`)
    .sort()
    .join(',')
  return `${nodeIds}|${edgeKeys}`
}

/**
 * Converts VueFlow elements to API format for backend
 */
function elementsToApiFormat(elements) {
  const nodes = elements
    .filter(el => el.id && !el.source && !el.target)
    .map(node => ({
      id: node.id,
      moduleId: node.data?.module || '',
      params: node.data?.params || {},
      data: {
        module: node.data?.module || ''
      }
    }))

  const edges = elements
    .filter(el => el.source && el.target)
    .map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: edge.type || edge.data?.edgeType || null,
      data: edge.data || {}
    }))

  return { nodes, edges }
}

/**
 * Creates a computed property that finds all upstream nodes for a selected node
 * S-Grade: Uses pre-computed relations from backend
 *
 * @param {import('vue').Ref<Array>} elements - Reactive array of VueFlow elements (nodes + edges)
 * @param {import('vue').Ref<Object|null>} selectedNode - Reactive selected node object
 * @returns {import('vue').ComputedRef<Array>} Computed array of upstream step info
 */
export function usePreviousSteps(elements, selectedNode) {
  // Watch for element changes and pre-compute relations
  watch(
    () => elements.value,
    async (newElements) => {
      if (!newElements || newElements.length === 0) {
        graphRelationsCache.value = {}
        lastComputeHash.value = null
        return
      }

      const hash = computeElementsHash(newElements)
      if (hash === lastComputeHash.value) {
        return // No change
      }

      try {
        const apiData = elementsToApiFormat(newElements)
        if (apiData.nodes.length === 0) {
          graphRelationsCache.value = {}
          lastComputeHash.value = hash
          return
        }

        // S-Grade: Call backend for graph relations
        const result = await workflowAPI.computeGraphRelations(apiData)
        if (result.ok && result.relations) {
          graphRelationsCache.value = result.relations
          lastComputeHash.value = hash
        }
      } catch (err) {
        // Backend unavailable — show empty; don't duplicate graph logic in frontend
        graphRelationsCache.value = {}
        lastComputeHash.value = null
      }
    },
    { immediate: true, deep: true }
  )

  // Return computed that looks up from cache
  return computed(() => {
    if (!selectedNode.value) return []

    const nodeId = selectedNode.value.id
    const relations = graphRelationsCache.value[nodeId]

    if (relations?.predecessors) {
      const steps = [...relations.predecessors]

      // Inject loop context variables (e.g. ${loop.item}, ${loop.index})
      if (relations.loopContext?.variables) {
        for (const v of relations.loopContext.variables) {
          steps.push({
            id: v.path,
            label: v.label,
            module: '__loop_context__',
            expression: v.expression
          })
        }
      }

      return steps
    }

    return []
  })
}

/**
 * Get successors for a node (bonus utility)
 * S-Grade: Uses same pre-computed cache
 *
 * @param {import('vue').Ref<Object|null>} selectedNode - Reactive selected node object
 * @returns {import('vue').ComputedRef<Array>} Computed array of downstream step info
 */
export function useNextSteps(selectedNode) {
  return computed(() => {
    if (!selectedNode.value) return []

    const nodeId = selectedNode.value.id
    const relations = graphRelationsCache.value[nodeId]

    if (relations?.successors) {
      return relations.successors
    }

    return []
  })
}

export default usePreviousSteps
