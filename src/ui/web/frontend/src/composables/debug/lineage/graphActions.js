/**
 * Lineage Graph Actions
 *
 * S-Grade: Graph loading actions for lineage.
 * Single responsibility: Load swimlane and full graph views.
 */

import { lineageAPI } from '@/api/lineage'
import i18n from '@/i18n'

/**
 * Create graph loading actions
 * @param {Object} state - State refs
 * @param {Object} options - Options with onError callback
 * @returns {Object} Graph actions
 */
export function createGraphActions(state, options = {}) {
  const { onError } = options
  const { viewMode, swimlane, graph, isLoading, error } = state

  /**
   * Load swimlane view (Lineage View)
   */
  async function loadSwimlane(executionId, loadOptions = {}) {
    isLoading.value = true
    error.value = null

    try {
      const data = await lineageAPI.getSwimlaneView(executionId, loadOptions)
      swimlane.value = {
        sources: data.sources || [],
        transforms: data.transforms || [],
        sinks: data.sinks || [],
        dataEdges: data.dataEdges || [],
        stateNodes: data.stateNodes || [],
        groups: data.groups || []
      }
      viewMode.value = 'lineage'
      return { ok: true, data: swimlane.value }
    } catch (err) {
      error.value = err.message || err.userMessage || i18n.global.t('error.failedToLoadLineage')
      onError?.(err)
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load full graph (Execution View)
   */
  async function loadGraph(executionId, includeVariables = false) {
    isLoading.value = true
    error.value = null

    try {
      const data = await lineageAPI.getFullGraph(executionId, includeVariables)
      graph.value = {
        nodes: data.nodes || [],
        edges: data.edges || []
      }
      viewMode.value = 'execution'
      return { ok: true, data: graph.value }
    } catch (err) {
      error.value = err.message || err.userMessage || i18n.global.t('error.failedToLoadGraph')
      onError?.(err)
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  return {
    loadSwimlane,
    loadGraph
  }
}
