/**
 * Workflows API
 * Handle workflow-related API requests
 */

import { get, post, put, del } from './client'
import { API_ENDPOINTS } from './config'

export const workflowAPI = {
  /**
   * List all workflows
   *
   * S-Grade: Supports server-side enabled filtering.
   *
   * @param {Object} options - Query options
   * @param {boolean} options.enabled - Filter by enabled status
   * @returns {Promise<Object>} Workflows list with counts
   */
  async list(options = {}) {
    const params = new URLSearchParams()
    if (options.enabled !== undefined) {
      params.append('enabled', options.enabled)
    }
    if (options.tags) {
      params.append('tags', Array.isArray(options.tags) ? options.tags.join(',') : options.tags)
    }
    const query = params.toString() ? `?${params.toString()}` : ''
    return await get(`${API_ENDPOINTS.WORKFLOWS.LIST}${query}`)
  },

  /**
   * Get single workflow
   * @param {string} id - Workflow ID
   * @returns {Promise<Object>} Workflow data
   */
  async get(id) {
    return await get(API_ENDPOINTS.WORKFLOWS.GET(id))
  },

  /**
   * Create new workflow
   * @param {Object} workflow - Workflow data
   * @returns {Promise<Object>} Created workflow
   */
  async create(workflow) {
    return await post(API_ENDPOINTS.WORKFLOWS.CREATE, workflow)
  },

  /**
   * Update workflow
   * @param {string} id - Workflow ID
   * @param {Object} workflow - Update data
   * @returns {Promise<Object>} Updated workflow
   */
  async update(id, workflow) {
    return await put(API_ENDPOINTS.WORKFLOWS.UPDATE(id), workflow)
  },

  /**
   * Delete workflow
   * @param {string} id - Workflow ID
   * @returns {Promise<void>}
   */
  async delete(id) {
    return await del(API_ENDPOINTS.WORKFLOWS.DELETE(id))
  },

  /**
   * Execute workflow
   * @param {string} id - Workflow ID
   * @param {Object} params - Execution parameters
   * @returns {Promise<Object>} Execution result
   */
  async execute(id, params = {}) {
    return await post(API_ENDPOINTS.WORKFLOWS.EXECUTE(id), params)
  },

  /**
   * Run workflow directly (without saving)
   * Core only accepts YAML format
   * @param {string} workflowYaml - Workflow as YAML string
   * @param {Object} params - Runtime parameters
   * @param {Object} options - Execution options
   * @param {number} options.startStep - Start step index (0-based) for partial execution
   * @param {number} options.endStep - End step index (0-based) for partial execution
   * @param {Array<string>} options.breakpoints - Node IDs where execution should pause (Human Checkpoints)
   * @param {string} options.screenshotMode - Screenshot mode: "off", "on_error", "all"
   * @returns {Promise<Object>} Execution result
   */
  async run(workflowYaml, params = {}, options = {}) {
    const payload = { workflowYaml, params }
    if (options.startStep !== undefined) payload.startStep = options.startStep
    if (options.endStep !== undefined) payload.endStep = options.endStep
    if (options.breakpoints && options.breakpoints.length > 0) {
      payload.breakpoints = options.breakpoints
    }
    if (options.screenshotMode) {
      payload.screenshotMode = options.screenshotMode
    }
    return await post(API_ENDPOINTS.WORKFLOWS.RUN, payload)
  },

  /**
   * Convert backend steps to VueFlow elements
   * @param {Object} data - { steps: Array }
   * @returns {Promise<Object>} { ok, nodes, edges }
   */
  async stepsToVueFlow(data) {
    return await post('/workflows/steps-to-vueflow', data)
  },

  /**
   * Convert VueFlow elements to backend steps
   * @param {Object} data - { nodes: Array, edges: Array }
   * @returns {Promise<Object>} { ok, steps }
   */
  async vueFlowToSteps(data) {
    return await post('/workflows/vueflow-to-steps', data)
  },

  /**
   * Validate workflow connections using core API
   * @param {Object} workflow - Workflow with steps or nodes/edges
   * @returns {Promise<Object>} Validation result { valid, errors, warnings }
   */
  async validate(workflow) {
    return await post('/workflows/validate', workflow)
  },

  /**
   * Compute auto layout positions using backend
   * S-Grade: All graph computation on backend
   * @param {Object} data - Nodes and edges to layout
   * @param {Array} data.nodes - Array of node objects
   * @param {Array} data.edges - Array of edge objects
   * @returns {Promise<Object>} { ok, positions: { nodeId: { x, y } } }
   */
  async computeLayout(data) {
    return await post('/workflows/layout', data)
  },

  /**
   * Pre-compute graph relations (predecessors/successors) for all nodes
   * S-Grade: All graph traversal on backend
   * @param {Object} data - Nodes and edges
   * @param {Array} data.nodes - Array of node objects
   * @param {Array} data.edges - Array of edge objects
   * @returns {Promise<Object>} { ok, relations: { nodeId: { predecessors, successors } } }
   */
  async computeGraphRelations(data) {
    return await post('/workflows/graph-relations', data)
  }
}
