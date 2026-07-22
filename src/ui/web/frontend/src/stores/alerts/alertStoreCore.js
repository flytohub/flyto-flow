/**
 * Alert Store Core
 *
 * S-Grade: Alert management store using extracted helpers.
 * Manages alert rules, active alerts, and notification state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  fetchActiveAlertsApi, acknowledgeAlertApi, muteAlertApi,
  fetchRulesApi, createRuleApi, updateRuleApi, deleteRuleApi,
  fetchHistoryApi
} from './alertApiHelpers'
import {
  DEFAULT_PAGINATION, updateAlertCounts, updateRuleCounts,
  markAlertAcknowledged, updateRuleInList, removeById, resetAlertState
} from './alertStateHelpers'
import { asObject, asRecordArray } from '@/utils/dataBoundary'

export const useAlertStore = defineStore('alerts', () => {
  // ========== State ==========
  const activeAlerts = ref([])
  const rules = ref([])
  const history = ref([])
  const pagination = ref({ ...DEFAULT_PAGINATION })
  const isLoading = ref(false)
  const isLoadingRules = ref(false)
  const error = ref(null)

  // Backend-computed counts
  const activeCount = ref(0)
  const criticalCount = ref(0)
  const warningCount = ref(0)
  const enabledRulesCount = ref(0)
  const totalRulesCount = ref(0)

  // Count refs for helpers
  const alertCountRefs = { activeCount, criticalCount, warningCount }
  const ruleCountRefs = { enabledRulesCount, totalRulesCount }

  // ========== Getters ==========
  const hasActiveAlerts = computed(() => activeAlerts.value.length > 0)
  const hasRules = computed(() => rules.value.length > 0)

  // ========== Actions ==========
  async function fetchActiveAlerts() {
    isLoading.value = true
    error.value = null
    const result = await fetchActiveAlertsApi()
    const normalized = asObject(result)
    if (normalized.ok) {
      activeAlerts.value = asRecordArray(normalized.alerts)
      updateAlertCounts(alertCountRefs, normalized)
    } else {
      error.value = normalized.error
    }
    isLoading.value = false
    return result
  }

  async function acknowledgeAlert(alertId) {
    isLoading.value = true
    error.value = null
    const result = await acknowledgeAlertApi(alertId)
    const normalized = asObject(result)
    if (normalized.ok) {
      markAlertAcknowledged(activeAlerts.value, alertId)
    } else {
      error.value = normalized.error
    }
    isLoading.value = false
    return result
  }

  async function muteAlert(alertId, duration = 60) {
    isLoading.value = true
    error.value = null
    const result = await muteAlertApi(alertId, duration)
    const normalized = asObject(result)
    if (normalized.ok) {
      removeById(activeAlerts.value, alertId)
    } else {
      error.value = normalized.error
    }
    isLoading.value = false
    return result
  }

  async function fetchRules() {
    isLoadingRules.value = true
    error.value = null
    const result = await fetchRulesApi()
    const normalized = asObject(result)
    if (normalized.ok) {
      rules.value = asRecordArray(normalized.rules)
      updateRuleCounts(ruleCountRefs, normalized)
    } else {
      error.value = normalized.error
    }
    isLoadingRules.value = false
    return result
  }

  async function createRule(ruleData) {
    isLoadingRules.value = true
    error.value = null
    const result = await createRuleApi(ruleData)
    const normalized = asObject(result)
    const rule = asObject(normalized.rule)
    if (normalized.ok && Object.keys(rule).length > 0) {
      rules.value.push(rule)
    } else {
      error.value = normalized.error
    }
    isLoadingRules.value = false
    return result
  }

  async function updateRule(ruleId, ruleData) {
    isLoadingRules.value = true
    error.value = null
    const result = await updateRuleApi(ruleId, ruleData)
    const normalized = asObject(result)
    const rule = asObject(normalized.rule)
    if (normalized.ok && Object.keys(rule).length > 0) {
      updateRuleInList(rules.value, ruleId, rule)
    } else {
      error.value = normalized.error
    }
    isLoadingRules.value = false
    return result
  }

  async function deleteRule(ruleId) {
    isLoadingRules.value = true
    error.value = null
    const result = await deleteRuleApi(ruleId)
    const normalized = asObject(result)
    if (normalized.ok) {
      removeById(rules.value, ruleId)
    } else {
      error.value = normalized.error
    }
    isLoadingRules.value = false
    return result
  }

  async function toggleRule(ruleId) {
    const rule = rules.value.find(r => r.id === ruleId)
    if (!rule) return { ok: false, error: 'Rule not found' }
    return updateRule(ruleId, { enabled: !rule.enabled })
  }

  async function fetchHistory(params = {}) {
    isLoading.value = true
    error.value = null
    const result = await fetchHistoryApi({
      page: params.page || pagination.value.page,
      limit: params.limit || pagination.value.limit
    })
    const normalized = asObject(result)
    if (normalized.ok) {
      history.value = asRecordArray(normalized.history)
      pagination.value = {
        ...asObject(pagination.value),
        ...asObject(normalized.pagination)
      }
    } else {
      error.value = normalized.error
    }
    isLoading.value = false
    return result
  }

  async function setPage(page) {
    pagination.value.page = page
    await fetchHistory({ page })
  }

  function clearError() {
    error.value = null
  }

  function reset() {
    resetAlertState({
      activeAlerts, rules, history, pagination,
      isLoading, isLoadingRules, error,
      activeCount, criticalCount, warningCount,
      enabledRulesCount, totalRulesCount
    })
  }

  return {
    // State
    activeAlerts, rules, history, pagination, isLoading, isLoadingRules, error,
    activeCount, criticalCount, warningCount, enabledRulesCount, totalRulesCount,
    // Getters
    hasActiveAlerts, hasRules,
    // Actions
    fetchActiveAlerts, acknowledgeAlert, muteAlert,
    fetchRules, createRule, updateRule, deleteRule, toggleRule,
    fetchHistory, setPage, clearError, reset
  }
})
