// DEPRECATED: Not used by any component
/**
 * Versioning API
 * API module for module version management
 */

import { get, post, del } from './client'

export const versioningAPI = {
  /**
   * List all versions of a module
   * @param {string} moduleId - Module ID
   * @returns {Promise<Object>} Versions list
   */
  async listVersions(moduleId) {
    return get(`/versioning/modules/${encodeURIComponent(moduleId)}/versions`)
  },

  /**
   * Get latest version of a module
   * @param {string} moduleId - Module ID
   * @returns {Promise<Object>} Latest version info
   */
  async getLatestVersion(moduleId) {
    return get(`/versioning/modules/${encodeURIComponent(moduleId)}/latest`)
  },

  /**
   * Resolve version from constraint
   * @param {string} moduleId - Module ID
   * @param {string} constraint - Version constraint (e.g., ^1.0.0, ~2.1.0)
   * @returns {Promise<Object>} Resolved version
   */
  async resolveVersion(moduleId, constraint) {
    return get(`/versioning/modules/${encodeURIComponent(moduleId)}/resolve?constraint=${encodeURIComponent(constraint)}`)
  },

  /**
   * Get module metadata for a specific version
   * @param {string} moduleId - Module ID
   * @param {string} version - Version string
   * @returns {Promise<Object>} Module metadata
   */
  async getModuleMetadata(moduleId, version) {
    return get(`/versioning/modules/${encodeURIComponent(moduleId)}/versions/${version}/metadata`)
  },

  /**
   * Get version locks for a workflow
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<Object>} Version locks map
   */
  async getWorkflowLocks(workflowId) {
    return get(`/versioning/workflows/${workflowId}/locks`)
  },

  /**
   * Set a version lock for a workflow
   * @param {string} workflowId - Workflow ID
   * @param {string} moduleId - Module ID to lock
   * @param {string} version - Version to lock to
   * @returns {Promise<Object>} Lock result
   */
  async setWorkflowLock(workflowId, moduleId, version) {
    return post(`/versioning/workflows/${workflowId}/locks`, {
      moduleId,
      version
    })
  },

  /**
   * Remove a version lock
   * @param {string} workflowId - Workflow ID
   * @param {string} moduleId - Module ID to unlock
   * @returns {Promise<Object>} Unlock result
   */
  async removeWorkflowLock(workflowId, moduleId) {
    return del(`/versioning/workflows/${workflowId}/locks/${encodeURIComponent(moduleId)}`)
  },

  /**
   * Get changelog for a module version
   * @param {string} moduleId - Module ID
   * @param {string} version - Version string
   * @returns {Promise<Object>} Changelog entries
   */
  async getChangelog(moduleId, version) {
    return get(`/versioning/modules/${encodeURIComponent(moduleId)}/versions/${version}/changelog`)
  },

  /**
   * Check for available updates
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<Object>} Available updates
   */
  async checkUpdates(workflowId) {
    return get(`/versioning/workflows/${workflowId}/updates`)
  }
}

export default versioningAPI
