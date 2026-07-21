/**
 * useLineage Core Composable
 *
 * S-Grade: Main lineage composable that composes all modules.
 * Single responsibility: Compose and expose lineage functionality.
 */

import { readonly } from 'vue'
import { createLineageState, createLineageComputed, getEmptySwimlane } from './state'
import { createGraphActions } from './graphActions'
import { createFocusActions } from './focusActions'
import { createItemLineageActions } from './itemLineageActions'

/**
 * Lineage composable for data lineage graph state and operations
 *
 * Supports dual view:
 * - Lineage View: Sources | Transforms | Sinks (swimlane layout)
 * - Execution View: Full graph with control flow (debug mode)
 *
 * @param {Object} options
 * @param {Function} options.onError - Error callback
 * @returns {Object} Lineage state and actions
 */
export function useLineage(options = {}) {
  // Create state
  const state = createLineageState()

  // Create computed properties
  const computed = createLineageComputed(state)

  // Create actions from modules
  const graphActions = createGraphActions(state, options)
  const focusActions = createFocusActions(state)
  const itemLineageActions = createItemLineageActions(state)

  /**
   * Switch between view modes
   */
  function setViewMode(mode) {
    state.viewMode.value = mode
  }

  /**
   * Clear all state
   */
  function clearAll() {
    state.swimlane.value = getEmptySwimlane()
    state.graph.value = { nodes: [], edges: [] }
    state.focusedNode.value = null
    state.focusData.value = null
    state.selectedNode.value = null
    state.dependencies.value = []
    state.highlightedPath.value = []
    state.itemLineage.value = { trackedOutputs: [], totalItemsTracked: 0 }
    state.selectedItemOrigins.value = null
    state.error.value = null
  }

  return {
    // State (readonly for external)
    viewMode: readonly(state.viewMode),
    swimlane: readonly(state.swimlane),
    graph: readonly(state.graph),
    focusedNode: readonly(state.focusedNode),
    focusData: readonly(state.focusData),
    selectedNode: state.selectedNode,
    dependencies: readonly(state.dependencies),
    highlightedPath: readonly(state.highlightedPath),
    isLoading: readonly(state.isLoading),
    error: readonly(state.error),

    // Item-level lineage state
    itemLineage: readonly(state.itemLineage),
    selectedItemOrigins: readonly(state.selectedItemOrigins),

    // Computed
    ...computed,

    // Graph actions
    ...graphActions,

    // Focus actions
    ...focusActions,

    // Item lineage actions
    ...itemLineageActions,

    // Utility actions
    setViewMode,
    clearAll
  }
}

export default useLineage
