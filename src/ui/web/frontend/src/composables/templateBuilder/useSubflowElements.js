/**
 * Subflow Elements Composable
 *
 * Manages elements (nodes/edges) for nested subflows within container nodes.
 * Handles synchronization between subflow tabs and parent container nodes.
 *
 * Single Responsibility: Subflow element state management and parent sync
 */

import { ref, computed } from 'vue'

/**
 * @param {Object} options
 * @param {Ref<Array>} options.elements - Main workflow elements
 * @param {Ref<number>} options.currentDepth - Current navigation depth (0 = root)
 * @param {Ref<string>} options.currentFlowId - Current active flow ID
 * @param {Ref<Object>} options.activeSubflowTab - Active subflow tab data
 * @param {Ref<Array>} options.subflowBreadcrumbs - Navigation breadcrumbs
 */
export function useSubflowElements({
  elements,
  currentDepth,
  currentFlowId,
  activeSubflowTab,
  subflowBreadcrumbs
}) {
  // Map: flowId -> elements array
  const subflowElementsMap = ref(new Map())

  /**
   * Get elements for the current active flow
   */
  const displayElements = computed({
    get: () => {
      // Root level returns main elements
      if (currentDepth.value === 0) {
        return elements.value
      }
      // Subflow returns cached elements
      const flowId = currentFlowId.value
      return subflowElementsMap.value.get(flowId) || []
    },
    set: (newElements) => {
      if (currentDepth.value === 0) {
        elements.value = newElements
      } else {
        const flowId = currentFlowId.value
        subflowElementsMap.value.set(flowId, newElements)
        syncSubflowToParent(flowId, newElements)
      }
    }
  })

  /**
   * Sync subflow elements back to parent container node
   * Uses transactional approach: prepare all changes first, then apply atomically
   * @returns {boolean} True if sync succeeded, false otherwise
   */
  function syncSubflowToParent(flowId, subflowElements) {
    // Phase 1: Validate all preconditions
    const activeTabData = activeSubflowTab.value
    if (!activeTabData || !activeTabData.parentNodeId) {
      return false
    }

    // Get parent level elements
    const parentFlowId = subflowBreadcrumbs.value[subflowBreadcrumbs.value.length - 2]?.id
    const isNestedSubflow = parentFlowId && currentDepth.value > 1
    let parentElements = isNestedSubflow
      ? subflowElementsMap.value.get(parentFlowId)
      : elements.value

    if (!parentElements) {
      return false
    }

    // Find container node
    const containerNodeIndex = parentElements.findIndex(
      el => el.id === activeTabData.parentNodeId
    )
    if (containerNodeIndex === -1) {
      return false
    }

    const containerNode = parentElements[containerNodeIndex]

    // Phase 2: Prepare all updates (no mutations yet)
    const nodes = subflowElements.filter(el => el.id && !el.source)
    const edges = subflowElements.filter(el => el.source && el.target)

    // Prepare updated container node
    const updatedNode = {
      ...containerNode,
      data: {
        ...containerNode.data,
        params: {
          ...containerNode.data?.params,
          subflow: { nodes, edges }
        }
      }
    }

    // Prepare new parent elements array
    const newParentElements = parentElements.map((el, i) =>
      i === containerNodeIndex ? updatedNode : el
    )

    // Phase 3: Apply changes atomically (single assignment)
    try {
      if (isNestedSubflow) {
        subflowElementsMap.value.set(parentFlowId, newParentElements)
      } else {
        elements.value = newParentElements
      }
      return true
    } catch (error) {
      console.error('[syncSubflowToParent] Failed to apply changes:', error)
      return false
    }
  }

  /**
   * Initialize subflow elements when opening a container
   * @param {string} flowId - Flow identifier
   * @param {Array} nodes - Subflow nodes
   * @param {Array} edges - Subflow edges
   */
  function initSubflowElements(flowId, nodes, edges) {
    const subflowElements = [...(nodes || []), ...(edges || [])]
    subflowElementsMap.value.set(flowId, subflowElements)
  }

  /**
   * Clear subflow elements for a flow
   */
  function clearSubflowElements(flowId) {
    subflowElementsMap.value.delete(flowId)
  }

  /**
   * Clear all subflow elements
   */
  function clearAllSubflows() {
    subflowElementsMap.value.clear()
  }

  return {
    displayElements,
    subflowElementsMap,
    initSubflowElements,
    clearSubflowElements,
    clearAllSubflows,
    syncSubflowToParent
  }
}
