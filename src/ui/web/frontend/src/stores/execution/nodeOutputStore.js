/**
 * Node Output Store
 *
 * S-Grade: Node execution outputs management.
 * Single responsibility: store and retrieve node outputs.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNodeOutputStore = defineStore('nodeOutput', () => {
  // ========== State ==========
  const nodeOutputs = ref({}) // { nodeId: { output, status, fetchedAt } }
  const nodeDisplayOutputs = ref({}) // { nodeId: [{ type, title, dataUri, content, stepId }, ...] }

  // ========== Actions ==========

  /**
   * Set output for a node
   * @param {string} nodeId - Node ID
   * @param {Object} data - Output data { output, status, durationMs, startedAt, inputs, error }
   */
  function setNodeOutput(nodeId, data) {
    nodeOutputs.value[nodeId] = {
      output: data.output,
      status: data.status,
      fetchedAt: Date.now(),
      durationMs: data.durationMs ?? null,
      startedAt: data.startedAt ?? null,
      inputs: data.inputs ?? null,
      error: data.error ?? null
    }
  }

  /**
   * Update outputs from state variables
   * Handles both formats:
   * - { nodeId: { output, status } } (structured)
   * - { nodeId: <raw_value> } (engine variables)
   * @param {Object} variables - State variables
   */
  function updateFromState(variables) {
    if (!variables) return

    Object.entries(variables).forEach(([nodeId, data]) => {
      if (data === null || data === undefined) return
      // Structured format: { output: ..., status: ... }
      if (typeof data === 'object' && !Array.isArray(data) && 'output' in data) {
        setNodeOutput(nodeId, data)
      } else {
        // Raw value format from engine variables — wrap it
        setNodeOutput(nodeId, {
          output: data,
          status: 'completed'
        })
      }
    })
  }

  /**
   * Get output for a specific node
   * @param {string} nodeId - Node ID
   * @returns {*} Node output or null
   */
  function getNodeOutput(nodeId) {
    return nodeOutputs.value[nodeId]?.output ?? null
  }

  /**
   * Get full output info for a node (including status and fetchedAt)
   * @param {string} nodeId - Node ID
   * @returns {Object|null} Full output info
   */
  function getNodeOutputInfo(nodeId) {
    return nodeOutputs.value[nodeId] || null
  }

  /**
   * Check if node has output
   * @param {string} nodeId - Node ID
   * @returns {boolean}
   */
  function hasOutput(nodeId) {
    return nodeId in nodeOutputs.value
  }

  /**
   * Get execution duration for a node
   * @param {string} nodeId - Node ID
   * @returns {number|null} Duration in milliseconds
   */
  function getNodeDuration(nodeId) {
    return nodeOutputs.value[nodeId]?.durationMs ?? null
  }

  /**
   * Get inputs for a node
   * @param {string} nodeId - Node ID
   * @returns {*} Node inputs or null
   */
  function getNodeInputs(nodeId) {
    return nodeOutputs.value[nodeId]?.inputs ?? null
  }

  /**
   * Get error for a node
   * @param {string} nodeId - Node ID
   * @returns {Object|null} Error object with message and optional traceback
   */
  function getNodeError(nodeId) {
    return nodeOutputs.value[nodeId]?.error ?? null
  }

  /**
   * Get start time for a node
   * @param {string} nodeId - Node ID
   * @returns {string|null} ISO timestamp or null
   */
  function getNodeStartedAt(nodeId) {
    return nodeOutputs.value[nodeId]?.startedAt ?? null
  }

  /**
   * Update display outputs from the flat list returned by polling API.
   * Groups items by stepId so each node can retrieve its own display outputs.
   * @param {Array} displayOutputs - Flat array of display output items
   */
  function updateDisplayOutputsFromList(displayOutputs) {
    if (!displayOutputs || displayOutputs.length === 0) return
    const grouped = {}
    for (const item of displayOutputs) {
      const stepId = item.stepId || item.step_id
      if (!stepId) continue
      if (!grouped[stepId]) grouped[stepId] = []
      grouped[stepId].push(item)
    }
    nodeDisplayOutputs.value = grouped
  }

  /**
   * Get display outputs for a specific node
   * @param {string} nodeId - Node ID
   * @returns {Array} Display output items for this node
   */
  function getNodeDisplayOutputs(nodeId) {
    return nodeDisplayOutputs.value[nodeId] || []
  }

  /**
   * Clear output for a specific node
   * @param {string} nodeId - Node ID
   */
  function clearNodeOutput(nodeId) {
    delete nodeOutputs.value[nodeId]
  }

  /**
   * Clear all node outputs (for new execution)
   */
  function clearAllOutputs() {
    nodeOutputs.value = {}
    nodeDisplayOutputs.value = {}
  }

  /**
   * Reset store
   */
  function reset() {
    nodeOutputs.value = {}
    nodeDisplayOutputs.value = {}
  }

  return {
    // State
    nodeOutputs,
    nodeDisplayOutputs,

    // Actions
    setNodeOutput,
    updateFromState,
    getNodeOutput,
    getNodeOutputInfo,
    hasOutput,
    getNodeDuration,
    getNodeInputs,
    getNodeError,
    getNodeStartedAt,
    updateDisplayOutputsFromList,
    getNodeDisplayOutputs,
    clearNodeOutput,
    clearAllOutputs,
    reset
  }
})
