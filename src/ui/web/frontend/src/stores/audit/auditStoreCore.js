/**
 * Audit Store Core
 *
 * S-Grade: Main audit store.
 * Single responsibility: Compose audit functionality.
 */

import { defineStore } from 'pinia'
import { createAuditState, createAuditGetters } from './state'
import { createAuditActions, createUtilityActions } from './actions'

export const useAuditStore = defineStore('audit', () => {
  // Create state
  const state = createAuditState()

  // Create getters
  const getters = createAuditGetters(state)

  // Create actions
  const auditActions = createAuditActions(state)
  const utilityActions = createUtilityActions(state, auditActions.fetchLogs)

  return {
    // State
    ...state,

    // Getters
    ...getters,

    // Actions
    ...auditActions,
    ...utilityActions,
  }
})
