/**
 * Item-Level Lineage Actions
 *
 * S-Grade: Item-level lineage tracking actions.
 * Single responsibility: Track individual items through pipeline.
 * Similar to n8n's pairedItem concept.
 */

import { lineageAPI } from '@/api/lineage'
import i18n from '@/i18n'

/**
 * Create item-level lineage actions
 * @param {Object} state - State refs
 * @returns {Object} Item lineage actions
 */
export function createItemLineageActions(state) {
  const { itemLineage, selectedItemOrigins, isLoading, error } = state

  /**
   * Load item-level lineage for an execution
   */
  async function loadItemLineage(executionId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await lineageAPI.getItemLevelLineage(executionId)
      itemLineage.value = {
        trackedOutputs: data.trackedOutputs || [],
        totalItemsTracked: data.totalItemsTracked || 0
      }
      return { ok: true, data: itemLineage.value }
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToLoadItemLineage')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get item-level origins for a specific step output
   */
  async function loadStepItemOrigins(executionId, stepId, portId = 'default') {
    try {
      const data = await lineageAPI.getStepItemOrigins(executionId, stepId, portId)
      selectedItemOrigins.value = data
      return { ok: true, data }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  /**
   * Trace the origin of a specific variable path
   * Supports paths like "user.address.city" or "items[0].name"
   */
  async function traceVariableOrigin(executionId, variablePath) {
    isLoading.value = true
    try {
      const data = await lineageAPI.traceVariableOrigin(executionId, variablePath)
      return { ok: true, data }
    } catch (err) {
      return { ok: false, error: err.message }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get the origin of a specific item in an array output
   * @param {string} stepId - The step that produced the output
   * @param {number} index - The index of the item in the array
   */
  function getItemOrigin(stepId, index) {
    const output = itemLineage.value.trackedOutputs.find(o => o.stepId === stepId)
    if (output && output.itemOrigins && output.itemOrigins[index]) {
      return output.itemOrigins[index]
    }
    return output?.origin || null
  }

  /**
   * Get all items from a specific source node
   * Useful for understanding which items came from which source
   */
  function getItemsFromSource(sourceNodeId) {
    const items = []
    for (const output of itemLineage.value.trackedOutputs) {
      if (output.itemOrigins) {
        output.itemOrigins.forEach((origin, index) => {
          if (origin.nodeId === sourceNodeId) {
            items.push({
              stepId: output.stepId,
              index,
              origin
            })
          }
        })
      } else if (output.origin?.nodeId === sourceNodeId) {
        items.push({
          stepId: output.stepId,
          index: null,
          origin: output.origin
        })
      }
    }
    return items
  }

  return {
    loadItemLineage,
    loadStepItemOrigins,
    traceVariableOrigin,
    getItemOrigin,
    getItemsFromSource
  }
}
