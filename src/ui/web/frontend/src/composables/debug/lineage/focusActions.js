/**
 * Lineage Focus Actions
 *
 * S-Grade: Focus and selection actions for lineage.
 * Single responsibility: Node focus, selection, dependencies.
 */

import { lineageAPI } from '@/api/lineage'
import i18n from '@/i18n'

/**
 * Create focus and selection actions
 * @param {Object} state - State refs
 * @returns {Object} Focus actions
 */
export function createFocusActions(state) {
  const {
    focusedNode,
    focusData,
    selectedNode,
    dependencies,
    highlightedPath,
    isLoading,
    error
  } = state

  /**
   * Focus on a node (click to highlight upstream/downstream)
   */
  async function focusNode(executionId, nodeId, hops = 2) {
    if (focusedNode.value === nodeId) {
      // Toggle off
      clearFocus()
      return { ok: true, focused: false }
    }

    isLoading.value = true
    try {
      const data = await lineageAPI.getNodeFocus(executionId, nodeId, hops)
      focusedNode.value = nodeId
      focusData.value = data
      selectedNode.value = data
      return { ok: true, focused: true, data }
    } catch (err) {
      error.value = err.message
      return { ok: false, error: err.message }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Clear focus mode
   */
  function clearFocus() {
    focusedNode.value = null
    focusData.value = null
  }

  /**
   * Select a node for detail panel
   */
  function selectNode(node) {
    selectedNode.value = node
  }

  /**
   * Load dependencies for selected node
   */
  async function loadDependencies(executionId, stepId) {
    try {
      const data = await lineageAPI.getDependencies(executionId, stepId)
      dependencies.value = data.dependencies || []
      return { ok: true, data: dependencies.value }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  /**
   * Trace a variable through the execution
   */
  async function traceVariable(executionId, variableName) {
    isLoading.value = true
    error.value = null

    try {
      const data = await lineageAPI.getVariableLineage(executionId, variableName)
      highlightedPath.value = data.consumedBy || []
      return { ok: true, data }
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToTraceVariable')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get impact analysis for a step
   */
  async function getImpact(executionId, stepId) {
    try {
      const data = await lineageAPI.getImpactAnalysis(executionId, stepId)
      return { ok: true, data }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  return {
    focusNode,
    clearFocus,
    selectNode,
    loadDependencies,
    traceVariable,
    getImpact
  }
}
