/**
 * Replay API
 * API module for execution replay system
 *
 * Note: API client automatically converts camelCase to snake_case.
 */

import { get, post } from './client'
import i18n from '@/i18n'

export const replayAPI = {
  /**
   * Validate if replay is possible from a step
   * @param {string} executionId - Execution ID
   * @param {string} fromStepId - Step ID to replay from
   * @returns {Promise<Object>} Validation result
   */
  async validateReplay(executionId, fromStepId) {
    return post(`/replay/validate`, {
      executionId,
      stepId: fromStepId
    })
  },

  /**
   * Start a replay execution
   * @param {string} executionId - Original execution ID
   * @param {Object} config - Replay configuration
   * @returns {Promise<Object>} Replay result with new execution ID
   */
  async startReplay(executionId, config = {}) {
    return post(`/replay/execute`, {
      executionId,
      stepId: config.fromStepId || config.stepId,
      modifiedContext: config.contextOverrides || {},
      ...config
    })
  },

  /**
   * Replay a single step with optional context overrides
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID to replay
   * @param {Object} contextOverrides - Context overrides
   * @returns {Promise<Object>} Step replay result
   */
  async replayStep(executionId, stepId, contextOverrides = {}) {
    return post(`/replay/step`, {
      executionId,
      stepId,
      modifiedContext: contextOverrides
    })
  },

  /**
   * Get replay execution status
   * @param {string} replayId - Replay execution ID
   * @returns {Promise<Object>} Execution status
   */
  async getReplayStatus(replayId) {
    return get(`/replay/status/${replayId}`)
  },

  /**
   * Poll for replay completion
   * @param {string} replayId - Replay execution ID
   * @param {Object} options - Polling options
   * @returns {Promise<Object>} Final status when complete
   */
  async waitForCompletion(replayId, options = {}) {
    const {
      interval = 1000,
      maxAttempts = 300,
      onProgress = null
    } = options

    for (let i = 0; i < maxAttempts; i++) {
      const status = await this.getReplayStatus(replayId)

      if (onProgress) {
        onProgress(status)
      }

      if (status.isCompleted || status.isFailed) {
        return status
      }

      await new Promise(resolve => setTimeout(resolve, interval))
    }

    return {
      ok: false,
      error: i18n.global.t('error.replayTimeout'),
      replayId: replayId
    }
  },

  /**
   * Cancel a running replay execution
   * @param {string} replayId - Replay execution ID to cancel
   * @returns {Promise<Object>} Cancellation result
   */
  async cancelReplay(replayId) {
    return post(`/executions/${replayId}/cancel`)
  },

  /**
   * Compare two executions
   * @param {string} originalId - Original execution ID
   * @param {string} replayId - Replay execution ID
   * @returns {Promise<Object>} Comparison result with diffs
   */
  async compareExecutions(originalId, replayId) {
    return post(`/replay/compare`, {
      originalExecutionId: originalId,
      replayExecutionId: replayId
    })
  },

  /**
   * Get replay history for an execution
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Replay history list
   */
  async getReplayHistory(executionId) {
    return get(`/replay/history`, {
      params: executionId ? { executionId } : {}
    })
  },

  /**
   * Get execution steps
   * @param {string} executionId - Execution ID
   * @returns {Promise<Object>} Steps list
   */
  async getExecutionSteps(executionId) {
    return get(`/replay/${executionId}/steps`)
  },

  /**
   * Get context at step
   * @param {string} executionId - Execution ID
   * @param {string} stepId - Step ID
   * @param {boolean} before - Get context before (true) or after (false)
   * @returns {Promise<Object>} Context data
   */
  async getContextAtStep(executionId, stepId, before = true) {
    return get(`/replay/${executionId}/context-at/${stepId}`, {
      params: { before }
    })
  }
}

export default replayAPI
