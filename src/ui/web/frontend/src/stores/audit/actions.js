/**
 * Audit Store Actions
 *
 * S-Grade: Audit log operations.
 * Single responsibility: Fetch, verify, and export audit logs.
 */

import { auditAPI } from '@/api/audit'
import { useOrganizationStore } from '@/stores/organizationStore'
import { asBoolean, asObject, asRecordArray } from '@/utils/dataBoundary'

/**
 * Get current organization ID
 * @returns {string|null}
 */
function getOrganizationId() {
  const orgStore = useOrganizationStore()
  return orgStore.organization?.id || null
}

/**
 * Create audit log actions
 * @param {Object} state - State refs
 * @returns {Object} Action functions
 */
export function createAuditActions(state) {
  const {
    logs,
    currentLog,
    verificationStatus,
    stats,
    pagination,
    filters,
    isLoading,
    isVerifying,
    error
  } = state

  /**
   * Fetch audit logs
   */
  async function fetchLogs(params = {}) {
    isLoading.value = true
    error.value = null

    const organizationId = getOrganizationId()
    if (!organizationId) {
      error.value = 'No organization selected'
      isLoading.value = false
      return { ok: false, error: error.value }
    }

    try {
      const result = await auditAPI.getLogs({
        organization_id: organizationId,
        page: params.page || pagination.value.page,
        limit: params.limit || pagination.value.limit,
        actor_id: params.userId || filters.value.userId,
        action: params.action || filters.value.action,
        resource_type: params.resourceType || filters.value.resourceType,
        start_time: params.startDate || filters.value.startDate,
        end_time: params.endDate || filters.value.endDate
      })

      const normalized = asObject(result)
      if (normalized.ok) {
        logs.value = asRecordArray(normalized.logs)
        pagination.value = {
          ...asObject(pagination.value),
          ...asObject(normalized.pagination)
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch audit logs'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch a single audit log
   */
  async function fetchLog(logId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await auditAPI.getLog(logId)
      const normalized = asObject(result)
      if (normalized.ok) {
        const log = asObject(normalized.log)
        currentLog.value = Object.keys(log).length > 0 ? log : null
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch audit log'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Verify audit chain integrity
   */
  async function verifyChain() {
    isVerifying.value = true
    error.value = null

    const organizationId = getOrganizationId()
    if (!organizationId) {
      error.value = 'No organization selected'
      isVerifying.value = false
      return { ok: false, error: error.value }
    }

    try {
      const result = await auditAPI.verifyChain({ organization_id: organizationId })
      const normalized = asObject(result)
      if (normalized.ok) {
        verificationStatus.value = {
          verified: asBoolean(normalized.verified, false),
          verifiedAt: new Date().toISOString(),
          details: asObject(normalized.details)
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to verify chain'
      return { ok: false, error: error.value }
    } finally {
      isVerifying.value = false
    }
  }

  /**
   * Fetch audit stats
   */
  async function fetchStats() {
    isLoading.value = true
    error.value = null

    const organizationId = getOrganizationId()
    if (!organizationId) {
      error.value = 'No organization selected'
      isLoading.value = false
      return { ok: false, error: error.value }
    }

    try {
      const result = await auditAPI.getStats({ organization_id: organizationId })
      const normalized = asObject(result)
      if (normalized.ok) {
        stats.value = asObject(normalized.stats)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || 'Failed to fetch stats'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Export audit logs
   */
  async function exportLogs(format = 'csv') {
    isLoading.value = true
    error.value = null

    const organizationId = getOrganizationId()
    if (!organizationId) {
      error.value = 'No organization selected'
      isLoading.value = false
      return null
    }

    try {
      const result = await auditAPI.exportLogs({
        organization_id: organizationId,
        format,
        start_time: filters.value.startDate,
        end_time: filters.value.endDate
      })
      return result
    } catch (err) {
      error.value = err.message || 'Failed to export logs'
      return null
    } finally {
      isLoading.value = false
    }
  }

  return {
    fetchLogs,
    fetchLog,
    verifyChain,
    fetchStats,
    exportLogs,
  }
}

/**
 * Create filter and utility actions
 * @param {Object} state - State refs
 * @param {Function} fetchLogs - Fetch logs function
 * @returns {Object} Utility action functions
 */
export function createUtilityActions(state, fetchLogs) {
  const {
    logs,
    currentLog,
    verificationStatus,
    stats,
    pagination,
    filters,
    isLoading,
    isVerifying,
    error
  } = state

  /**
   * Set filters and fetch logs
   */
  async function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1
    await fetchLogs()
  }

  /**
   * Set page and fetch logs
   */
  async function setPage(page) {
    pagination.value.page = page
    await fetchLogs({ page })
  }

  /**
   * Clear current log
   */
  function clearCurrentLog() {
    currentLog.value = null
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset state
   */
  function reset() {
    logs.value = []
    currentLog.value = null
    verificationStatus.value = null
    stats.value = null
    pagination.value = { page: 1, limit: 50, total: 0, totalPages: 1 }
    filters.value = {
      userId: null,
      action: null,
      resourceType: null,
      startDate: null,
      endDate: null,
      search: ''
    }
    isLoading.value = false
    isVerifying.value = false
    error.value = null
  }

  return {
    setFilters,
    setPage,
    clearCurrentLog,
    clearError,
    reset,
  }
}
