/**
 * Enterprise Features API
 *
 * API services for enterprise-only features:
 * - Orchestrator (Robots, Jobs)
 * - Queues (Work Queues, Transactions)
 * - State Machine
 * - Process Mining
 * - IDP (Intelligent Document Processing)
 * - RPA (Desktop Automation)
 */

import { get, post } from './client'
import {
  normalizeRobot,
  normalizeRobotStats,
  normalizeJob,
  normalizeQueue,
  normalizeQueueStats,
  normalizeTransaction,
  normalizeStateMachine,
  normalizeStateMachineStats,
  normalizeProcessStats,
  normalizeDocument,
  normalizeIdpModel,
  normalizeIdpStats,
  normalizeAgent,
  normalizeAgentStats,
  normalizeRecording,
  normalizeProcess,
  normalizeDiscoveryResult
} from './normalizers/enterprise'

// =============================================================================
// Orchestrator - Robots
// =============================================================================

/**
 * List registered robots
 * @param {Object} params - Query parameters
 * @param {string} [params.status] - Filter by status (online, busy, offline)
 * @param {number} [params.skip] - Skip count for pagination
 * @param {number} [params.limit] - Limit count for pagination
 * @returns {Promise<{items: Array}>}
 */
export async function listRobots(params = {}) {
  const result = await get('/enterprise/orchestrator/robots', { params })
  const items = (result?.items || result?.robots || result || []).map(normalizeRobot)
  return { ...result, items }
}

/**
 * Get robot statistics
 * @returns {Promise<{total: number, online: number, offline: number, busy: number}>}
 */
export async function getRobotStats() {
  const result = await get('/enterprise/orchestrator/robots/stats')
  return normalizeRobotStats(result || {})
}

/**
 * Create a new robot
 * @param {Object} data - Robot data
 * @returns {Promise<Object>}
 */
export async function createRobot(data) {
  return post('/enterprise/orchestrator/robots', data)
}

// =============================================================================
// Orchestrator - Jobs
// =============================================================================

/**
 * List scheduled jobs
 * @param {Object} params - Query parameters
 * @param {boolean} [params.isEnabled] - Filter by enabled status
 * @param {string} [params.robotId] - Filter by robot ID
 * @param {number} [params.skip] - Skip count for pagination
 * @param {number} [params.limit] - Limit count for pagination
 * @returns {Promise<{items: Array}>}
 */
export async function listJobs(params = {}) {
  const result = await get('/enterprise/orchestrator/jobs', { params })
  const items = (result?.items || result?.jobs || result || []).map(normalizeJob)
  return { ...result, items }
}

/**
 * Create a scheduled job
 * @param {Object} data - Job data
 * @returns {Promise<Object>}
 */
export async function createJob(data) {
  return post('/enterprise/orchestrator/jobs', data)
}

/**
 * Trigger a job manually
 * @param {string} jobId - Job ID
 * @returns {Promise<Object>}
 */
export async function triggerJob(jobId) {
  return post(`/enterprise/orchestrator/jobs/${jobId}/trigger`)
}

// =============================================================================
// Queues
// =============================================================================

/**
 * List work queues
 * @param {Object} params - Query parameters
 * @param {number} [params.skip] - Skip count for pagination
 * @param {number} [params.limit] - Limit count for pagination
 * @returns {Promise<{items: Array}>}
 */
export async function listQueues(params = {}) {
  const result = await get('/enterprise/queues', { params })
  const items = (result?.items || result?.queues || result || []).map(normalizeQueue)
  return { ...result, items }
}

/**
 * Get queue statistics
 * @returns {Promise<{totalItems: number, pending: number, processing: number, completed: number, failed: number}>}
 */
export async function getQueueStats() {
  const result = await get('/enterprise/queues/stats')
  return normalizeQueueStats(result || {})
}

/**
 * Create a work queue
 * @param {Object} data - Queue data
 * @returns {Promise<Object>}
 */
export async function createQueue(data) {
  return post('/enterprise/queues', data)
}

/**
 * List queue transactions
 * @param {Object} params - Query parameters
 * @param {string} [params.status] - Filter by status
 * @returns {Promise<{items: Array}>}
 */
export async function listTransactions(params = {}) {
  const result = await get('/enterprise/queues/transactions', { params })
  const items = (result?.items || result?.transactions || result || []).map(normalizeTransaction)
  return { ...result, items }
}

// =============================================================================
// State Machine
// =============================================================================

/**
 * List state machines
 * @param {Object} params - Query parameters
 * @param {boolean} [params.isActive] - Filter by active status
 * @param {number} [params.skip] - Skip count for pagination
 * @param {number} [params.limit] - Limit count for pagination
 * @returns {Promise<{items: Array}>}
 */
export async function listStateMachines(params = {}) {
  const result = await get('/enterprise/state-machines', { params })
  const items = (result?.items || result?.machines || result || []).map(normalizeStateMachine)
  return { ...result, items }
}

/**
 * Get state machine statistics
 * @returns {Promise<{machines: number, instances: number, activeInstances: number}>}
 */
export async function getStateMachineStats() {
  const result = await get('/enterprise/state-machines/stats')
  return normalizeStateMachineStats(result || {})
}

/**
 * Create a state machine
 * @param {Object} data - State machine definition
 * @returns {Promise<Object>}
 */
export async function createStateMachine(data) {
  return post('/enterprise/state-machines', data)
}

/**
 * Trigger a state transition
 * @param {string} instanceId - State machine instance ID
 * @param {string} event - Event to trigger
 * @param {Object} [data] - Additional data
 * @returns {Promise<Object>}
 */
export async function triggerTransition(instanceId, event, data = null) {
  return post(`/enterprise/state-machines/instances/${instanceId}/transition`, data, {
    params: { event }
  })
}

// =============================================================================
// Process Mining
// =============================================================================

/**
 * List discovered processes
 * @returns {Promise<{items: Array}>}
 */
export async function listProcesses() {
  const result = await get('/enterprise/mining/processes')
  const items = (result?.items || result?.processes || result || []).map(normalizeProcess)
  return { ...result, items }
}

/**
 * Get statistics for a process
 * @param {string} processName - Process name
 * @returns {Promise<Object>}
 */
export async function getProcessStats(processName) {
  const result = await get(`/enterprise/mining/processes/${encodeURIComponent(processName)}/stats`)
  return normalizeProcessStats(result || {})
}

/**
 * Discover process model from event logs
 * @param {Object} data - Discovery parameters
 * @returns {Promise<Object>}
 */
export async function discoverProcess(data) {
  const result = await post('/enterprise/mining/discover', data)
  const normalized = normalizeDiscoveryResult(result || {})
  return {
    ...normalized,
    stats: normalizeProcessStats(normalized.stats || {})
  }
}

// =============================================================================
// IDP (Intelligent Document Processing)
// =============================================================================

/**
 * List documents
 * @param {Object} params - Query parameters
 * @param {string} [params.status] - Filter by status
 * @param {number} [params.skip] - Skip count for pagination
 * @param {number} [params.limit] - Limit count for pagination
 * @returns {Promise<{items: Array}>}
 */
export async function listDocuments(params = {}) {
  const result = await get('/enterprise/idp/documents', { params })
  const items = (result?.items || result?.documents || result || []).map(normalizeDocument)
  return { ...result, items }
}

/**
 * Get document statistics
 * @returns {Promise<{total: number, pending: number, completed: number, failed: number}>}
 */
export async function getDocumentStats() {
  const result = await get('/enterprise/idp/documents/stats')
  return normalizeIdpStats(result || {})
}

/**
 * Create a document for processing
 * @param {Object} data - Document data
 * @returns {Promise<Object>}
 */
export async function createDocument(data) {
  return post('/enterprise/idp/documents', data)
}

/**
 * Process a document with an IDP model
 * @param {string} docId - Document ID
 * @param {string} [modelId] - Model ID to use for processing
 * @returns {Promise<Object>}
 */
export async function processDocument(docId, modelId = null) {
  const params = modelId ? { modelId } : {}
  return post(`/enterprise/idp/documents/${docId}/process`, {}, { params })
}

/**
 * List IDP models
 * @param {Object} params - Query parameters
 * @param {string} [params.modelType] - Filter by model type
 * @returns {Promise<{items: Array}>}
 */
export async function listIdpModels(params = {}) {
  const result = await get('/enterprise/idp/models', { params })
  const items = (result?.items || result?.models || result || []).map(normalizeIdpModel)
  return { ...result, items }
}

// =============================================================================
// RPA (Desktop Automation)
// =============================================================================

/**
 * List RPA desktop agents
 * @param {Object} params - Query parameters
 * @param {string} [params.status] - Filter by status
 * @returns {Promise<{items: Array}>}
 */
export async function listAgents(params = {}) {
  const result = await get('/enterprise/rpa/agents', { params })
  const items = (result?.items || result?.agents || result || []).map(normalizeAgent)
  return { ...result, items }
}

/**
 * Get RPA agent statistics
 * @returns {Promise<{total: number, online: number, offline: number, busy: number}>}
 */
export async function getAgentStats() {
  const result = await get('/enterprise/rpa/agents/stats')
  return normalizeAgentStats(result || {})
}

/**
 * Connect an RPA agent
 * @param {Object} data - Connection data
 * @returns {Promise<Object>}
 */
export async function connectAgent(data) {
  return post('/enterprise/rpa/agents/connect', data)
}

/**
 * List RPA recordings
 * @param {Object} params - Query parameters
 * @param {number} [params.skip] - Skip count for pagination
 * @param {number} [params.limit] - Limit count for pagination
 * @returns {Promise<{items: Array}>}
 */
export async function listRecordings(params = {}) {
  const result = await get('/enterprise/rpa/recordings', { params })
  const items = (result?.items || result?.recordings || result || []).map(normalizeRecording)
  return { ...result, items }
}

/**
 * Start RPA execution
 * @param {string} recordingId - Recording ID to execute
 * @param {string} agentId - Agent ID to run on
 * @returns {Promise<Object>}
 */
export async function startExecution(recordingId, agentId) {
  return post('/enterprise/rpa/executions', {}, {
    params: { recordingId, agentId }
  })
}

// =============================================================================
// Combined API Object
// =============================================================================

export const enterpriseAPI = {
  // Orchestrator - Robots
  listRobots,
  getRobotStats,
  createRobot,

  // Orchestrator - Jobs
  listJobs,
  createJob,
  triggerJob,

  // Queues
  listQueues,
  getQueueStats,
  createQueue,
  listTransactions,

  // State Machine
  listStateMachines,
  getStateMachineStats,
  createStateMachine,
  triggerTransition,

  // Process Mining
  listProcesses,
  getProcessStats,
  discoverProcess,

  // IDP
  listDocuments,
  getDocumentStats,
  createDocument,
  processDocument,
  listIdpModels,

  // RPA
  listAgents,
  getAgentStats,
  connectAgent,
  listRecordings,
  startExecution
}

export default enterpriseAPI
