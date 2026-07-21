// DEPRECATED: Not used by any component
/**
 * Lineage API
 * API module for data lineage tracking system
 *
 * Supports dual view:
 * - Swimlane View: Sources | Transforms | Sinks (for understanding data flow)
 * - Execution View: Full graph with control flow (for debugging)
 */

import { get, post } from './client'

export const lineageAPI = {
  /**
   * Get swimlane view for lineage visualization
   * Returns nodes organized into Sources | Transforms | Sinks lanes
   * @param {string} executionId - Execution ID
   * @param {Object} options - View options
   * @returns {Promise<Object>} Swimlane view data
   */
  async getSwimlaneView(executionId, options = {}) {
    try {
      const params = new URLSearchParams()
      if (options.includeControlFlow) params.append('include_control_flow', 'true')
      if (options.groupLoops === false) params.append('group_loops', 'false')
      const query = params.toString() ? `?${params.toString()}` : ''
      return await get(`/lineage/executions/${executionId}/swimlane${query}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get focused lineage for a specific node (click to focus)
   * Returns only upstream and downstream nodes within N hops
   * @param {string} executionId - Execution ID
   * @param {string} nodeId - Node ID to focus on
   * @param {number} hops - Number of hops (default 2)
   * @returns {Promise<Object>} Focus data with upstream/downstream
   */
  async getNodeFocus(executionId, nodeId, hops = 2) {
    try {
      return await get(`/lineage/executions/${executionId}/focus/${nodeId}?hops=${hops}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get lineage for a specific step
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @returns {Promise<Object>} Step lineage data
   */
  async getStepLineage(executionId, stepId) {
    try {
      return await get(`/lineage/executions/${executionId}/steps/${stepId}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get lineage for a variable
   * @param {string} executionId - Execution ID
   * @param {string} variableName - Variable name to trace
   * @returns {Promise<Object>} Variable lineage data
   */
  async getVariableLineage(executionId, variableName) {
    try {
      return await get(`/lineage/executions/${executionId}/variables/${encodeURIComponent(variableName)}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get full lineage graph for an execution (Execution View)
   * @param {string} executionId - Execution ID
   * @param {boolean} includeVariables - Include variable nodes
   * @returns {Promise<Object>} Full graph with nodes and edges
   */
  async getFullGraph(executionId, includeVariables = true) {
    try {
      return await get(`/lineage/executions/${executionId}/graph?include_variables=${includeVariables}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get dependencies for a step
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @returns {Promise<Object>} Dependencies data
   */
  async getDependencies(executionId, stepId) {
    try {
      return await get(`/lineage/executions/${executionId}/steps/${stepId}/dependencies`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get impact analysis for a step
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @returns {Promise<Object>} Impact analysis data
   */
  async getImpactAnalysis(executionId, stepId) {
    try {
      return await get(`/lineage/executions/${executionId}/steps/${stepId}/impact`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  // ==========================================================================
  // Item-Level Lineage (like n8n's pairedItem)
  // ==========================================================================

  /**
   * Get item-level lineage for an execution
   * Returns tracked outputs with origin information for each item
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Item-level lineage data
   */
  async getItemLevelLineage(executionId) {
    try {
      return await get(`/lineage/executions/${executionId}/item-lineage`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get item-level origins for a specific step output
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @param {string} portId - Port ID (default: "default")
   * @returns {Promise<Object>} Item origins for the step
   */
  async getStepItemOrigins(executionId, stepId, portId = 'default') {
    try {
      return await get(`/lineage/executions/${executionId}/steps/${stepId}/item-origins?port_id=${portId}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Trace the origin of a specific variable or path
   * Supports paths like "user.address.city" or "items[0].name"
   * @param {string} executionId - Execution ID
   * @param {string} variablePath - Variable path to trace
   * @returns {Promise<Object>} Origin trace data
   */
  async traceVariableOrigin(executionId, variablePath) {
    try {
      return await get(`/lineage/executions/${executionId}/trace/${encodeURIComponent(variablePath)}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  }
}

export default lineageAPI
