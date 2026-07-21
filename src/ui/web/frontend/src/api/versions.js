/**
 * Versions API - Phase 9 Version Control
 * Workflow version history and rollback endpoints
 */

import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import i18n from '@/i18n'

export const versionsAPI = {
  /**
   * Get version history for a workflow
   * @param {string} workflowId - Workflow ID
   * @returns {Promise<Object>}
   */
  async getVersions(workflowId) {
    try {
      const result = await get(ENDPOINTS.VERSIONS.LIST(workflowId))

      return {
        ok: true,
        versions: (result.versions || []).map(v => ({
          version: v.version,
          createdAt: v.createdAt,
          createdBy: v.createdBy,
          commitMessage: v.commitMessage,
          changesSummary: v.changesSummary,
          isCurrent: v.isCurrent || false,
          metadata: v.metadata || {}
        }))
      }
    } catch (err) {
      return { ok: false, error: err.message, versions: [] }
    }
  },

  /**
   * Get a specific version
   * @param {string} workflowId - Workflow ID
   * @param {number} versionNumber - Version number
   * @returns {Promise<Object>}
   */
  async getVersion(workflowId, versionNumber) {
    try {
      const result = await get(ENDPOINTS.VERSIONS.GET(workflowId, versionNumber))

      return {
        ok: true,
        version: {
          version: result.version,
          createdAt: result.createdAt,
          createdBy: result.createdBy,
          commitMessage: result.commitMessage,
          content: result.content,
          yaml: result.yaml,
          metadata: result.metadata || {}
        }
      }
    } catch (err) {
      return { ok: false, error: err.message, version: null }
    }
  },

  /**
   * Get diff between two versions
   * @param {string} workflowId - Workflow ID
   * @param {number} fromVersion - Source version number
   * @param {number} toVersion - Target version number
   * @returns {Promise<Object>}
   */
  async getDiff(workflowId, fromVersion, toVersion) {
    try {
      const result = await get(ENDPOINTS.VERSIONS.DIFF(workflowId), {
        params: { from: fromVersion, to: toVersion }
      })

      return {
        ok: true,
        diff: {
          fromVersion: result.fromVersion,
          toVersion: result.toVersion,
          changes: result.changes || [],
          unifiedDiff: result.unifiedDiff,
          stats: {
            additions: result.additions || 0,
            deletions: result.deletions || 0,
            modifications: result.modifications || 0
          }
        }
      }
    } catch (err) {
      return { ok: false, error: err.message, diff: null }
    }
  },

  /**
   * Rollback to a specific version
   * @param {string} workflowId - Workflow ID
   * @param {number} versionNumber - Version to rollback to
   * @returns {Promise<Object>}
   */
  async rollback(workflowId, versionNumber) {
    try {
      const result = await post(ENDPOINTS.VERSIONS.ROLLBACK(workflowId, versionNumber))

      return {
        ok: true,
        newVersion: result.newVersion,
        message: result.message || i18n.global.t('message.rollbackSuccessful')
      }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }
}

export default versionsAPI
