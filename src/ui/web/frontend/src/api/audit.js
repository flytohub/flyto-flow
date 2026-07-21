/**
 * Audit API - Phase 9 Audit Logs
 * Audit log retrieval and chain verification endpoints
 *
 * Note: snake_case → camelCase conversion is handled automatically
 * by the API client interceptor (api/client.js).
 */

import { get } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const auditAPI = {
  /**
   * Get audit logs with pagination and filters
   * @param {Object} params - Query parameters (must include organization_id)
   * @returns {Promise<Object>}
   */
  async getLogs(params = {}) {
    try {
      if (!params.organization_id) {
        return {
          ok: false,
          error: 'Organization ID is required',
          logs: [],
          pagination: { page: 1, limit: 50, total: 0, totalPages: 1 }
        }
      }
      const result = await get(ENDPOINTS.AUDIT.LIST, { params })

      // Handle both array response (feature-gated) and object response (public stub)
      const logs = Array.isArray(result) ? result : (result.logs || [])

      return {
        ok: true,
        logs: logs.map(log => ({
          id: log.id,
          sequenceNumber: log.sequenceNumber,
          timestamp: log.timestamp,
          userId: log.actorId,
          userType: log.actorType,
          ipAddress: log.actorIp,
          userAgent: log.actorUserAgent,
          action: log.action,
          resourceType: log.resourceType,
          resourceId: log.resourceId,
          changeSummary: log.changeSummary,
          oldValueHash: log.oldValueHash,
          newValueHash: log.newValueHash,
          hash: log.entryHash,
          prevHash: log.prevEntryHash,
          traceId: log.traceId,
          metadata: log.metadata || {}
        })),
        pagination: {
          page: result.page || 1,
          limit: result.limit || 50,
          total: logs.length,
          totalPages: result.totalPages || 1
        }
      }
    } catch (err) {
      return {
        ok: false,
        error: err.message,
        logs: [],
        pagination: { page: 1, limit: 50, total: 0, totalPages: 1 }
      }
    }
  },

  /**
   * Get a single audit log by ID
   * @param {string} logId - Log ID
   * @returns {Promise<Object>}
   */
  async getLog(logId) {
    try {
      const result = await get(ENDPOINTS.AUDIT.GET(logId))

      return {
        ok: true,
        log: {
          id: result.id,
          sequenceNumber: result.sequenceNumber,
          timestamp: result.timestamp,
          userId: result.actorId,
          userType: result.actorType,
          ipAddress: result.actorIp,
          userAgent: result.actorUserAgent,
          action: result.action,
          resourceType: result.resourceType,
          resourceId: result.resourceId,
          changeSummary: result.changeSummary,
          oldValueHash: result.oldValueHash,
          newValueHash: result.newValueHash,
          hash: result.entryHash,
          prevHash: result.prevEntryHash,
          traceId: result.traceId,
          metadata: result.metadata || {}
        }
      }
    } catch (err) {
      return { ok: false, error: err.message, log: null }
    }
  },

  /**
   * Verify audit chain integrity
   * @param {Object} params - Query parameters (must include organization_id)
   * @returns {Promise<Object>}
   */
  async verifyChain(params = {}) {
    try {
      if (!params.organization_id) {
        return { ok: false, error: 'Organization ID is required', verified: false }
      }
      const result = await get(ENDPOINTS.AUDIT.VERIFY, { params })

      return {
        ok: true,
        verified: result.isValid,
        details: {
          totalRecords: result.entriesChecked,
          verifiedRecords: result.entriesChecked,
          startSequence: result.startSequence,
          endSequence: result.endSequence,
          tamperingReports: result.tamperingReports || [],
          verifiedAt: result.verifiedAt,
          error: result.error
        }
      }
    } catch (err) {
      return { ok: false, error: err.message, verified: false }
    }
  },

  /**
   * Get audit statistics
   * @param {Object} params - Query parameters (must include organization_id)
   * @returns {Promise<Object>}
   */
  async getStats(params = {}) {
    try {
      if (!params.organization_id) {
        return { ok: false, error: 'Organization ID is required', stats: null }
      }
      const result = await get(ENDPOINTS.AUDIT.STATS, { params })

      return {
        ok: result.ok !== false,
        stats: {
          totalLogs: result.totalEntries || 0,
          actions: result.actions || {},
          resources: result.resources || {},
          topActors: result.topActors || {}
        }
      }
    } catch (err) {
      return { ok: false, error: err.message, stats: null }
    }
  },

  /**
   * Export audit logs
   * @param {Object} params - Export parameters (must include organization_id)
   * @returns {Promise<Blob>}
   */
  async exportLogs(params = {}) {
    try {
      if (!params.organization_id) {
        throw new Error('Organization ID is required')
      }
      const result = await get(ENDPOINTS.AUDIT.EXPORT, {
        params,
        responseType: 'blob'
      })
      return result
    } catch (err) {
      throw new Error(err.message || 'Failed to export logs')
    }
  }
}

export default auditAPI
