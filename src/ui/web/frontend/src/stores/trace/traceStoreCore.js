/**
 * Trace Store Core
 *
 * S-Grade: Main trace store.
 * Single responsibility: Compose trace functionality.
 */

import { defineStore } from 'pinia'
import { createTraceState, createTraceGetters } from './state'
import { createTraceActions, createUtilityActions } from './actions'

export const useTraceStore = defineStore('traces', () => {
  // Create state
  const state = createTraceState()

  // Create getters
  const getters = createTraceGetters(state)

  // Create actions
  const traceActions = createTraceActions(state)
  const utilityActions = createUtilityActions(state, traceActions.fetchTraces)

  return {
    // State
    ...state,

    // Getters
    ...getters,

    // Actions
    ...traceActions,
    ...utilityActions,
  }
})
