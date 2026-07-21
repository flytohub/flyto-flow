// DEPRECATED: Not used by any component
/**
 * Testing API
 * API module for workflow test framework
 */

import { get, post, del } from './client'

export const testingAPI = {
  /**
   * Load tests for a workflow
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<Object>} Tests list
   */
  async loadTests(workflowId) {
    return get(`/testing/workflows/${workflowId}/tests`)
  },

  /**
   * Run tests for a workflow
   * @param {string} workflowId - Workflow ID
   * @param {Array<string>} testNames - Optional specific test names to run
   * @returns {Promise<Object>} Test run result with ID
   */
  async runTests(workflowId, testNames = []) {
    return post(`/testing/workflows/${workflowId}/run`, {
      testNames
    })
  },

  /**
   * Run tests by tags
   * @param {string} workflowId - Workflow ID
   * @param {Array<string>} tags - Tags to filter tests
   * @returns {Promise<Object>} Test run result
   */
  async runTestsByTags(workflowId, tags) {
    return post(`/testing/workflows/${workflowId}/run-by-tags`, { tags })
  },

  /**
   * Get test result
   * @param {string} testRunId - Test run ID
   * @returns {Promise<Object>} Test results
   */
  async getTestResult(testRunId) {
    return get(`/testing/results/${testRunId}`)
  },

  /**
   * Get test report for a workflow
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<Object>} Test report with statistics
   */
  async getTestReport(workflowId) {
    return get(`/testing/workflows/${workflowId}/report`)
  },

  /**
   * Match data against a snapshot
   * @param {string} workflowId - Workflow ID
   * @param {string} snapshotName - Snapshot name
   * @param {*} actualData - Actual data to compare
   * @returns {Promise<Object>} Match result
   */
  async matchSnapshot(workflowId, snapshotName, actualData) {
    return post(`/testing/workflows/${workflowId}/snapshots/${snapshotName}/match`, {
      actual: actualData
    })
  },

  /**
   * Update a snapshot
   * @param {string} workflowId - Workflow ID
   * @param {string} snapshotName - Snapshot name
   * @param {*} data - New snapshot data
   * @returns {Promise<Object>} Update result
   */
  async updateSnapshot(workflowId, snapshotName, data) {
    return post(`/testing/workflows/${workflowId}/snapshots/${snapshotName}/update`, {
      data
    })
  },

  /**
   * List all snapshots for a workflow
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<Object>} Snapshots list
   */
  async listSnapshots(workflowId) {
    return get(`/testing/workflows/${workflowId}/snapshots`)
  },

  /**
   * Delete a snapshot
   * @param {string} workflowId - Workflow ID
   * @param {string} snapshotName - Snapshot name
   * @returns {Promise<Object>} Deletion result
   */
  async deleteSnapshot(workflowId, snapshotName) {
    return del(`/testing/workflows/${workflowId}/snapshots/${snapshotName}`)
  },

  /**
   * Get test coverage for a workflow
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<Object>} Coverage report
   */
  async getCoverage(workflowId) {
    return get(`/testing/workflows/${workflowId}/coverage`)
  }
}

export default testingAPI
