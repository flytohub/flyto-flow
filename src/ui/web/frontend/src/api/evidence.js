// DEPRECATED: Not used by any component
/**
 * Evidence API
 * API module for step evidence system
 */

import { get, post, del } from './client'

export const evidenceAPI = {
  /**
   * Get all evidence for an execution
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Execution evidence data
   */
  async getExecutionEvidence(executionId) {
    try {
      return await get(`/evidence/${executionId}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get evidence for a specific step
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @returns {Promise<Object>} Step evidence data
   */
  async getStepEvidence(executionId, stepId) {
    try {
      return await get(`/evidence/${executionId}/steps/${stepId}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Get screenshot URL for a step
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @returns {string} Screenshot URL
   */
  getScreenshotUrl(executionId, stepId) {
    return `/api/evidence/${executionId}/steps/${stepId}/screenshot`
  },

  /**
   * Get DOM snapshot URL for a step
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @returns {string} DOM snapshot URL
   */
  getDomUrl(executionId, stepId) {
    return `/api/evidence/${executionId}/steps/${stepId}/dom`
  },

  /**
   * Get context diff for a step
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @returns {Promise<Object>} Context diff data
   */
  async getContextDiff(executionId, stepId) {
    try {
      return await get(`/evidence/${executionId}/context-diff?step_id=${stepId}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  },

  /**
   * Delete evidence for an execution
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Deletion result
   */
  async deleteEvidence(executionId) {
    try {
      return await del(`/evidence/${executionId}`)
    } catch (err) {
      return { ok: false, error: err.userMessage || err.message }
    }
  }
}

export default evidenceAPI
