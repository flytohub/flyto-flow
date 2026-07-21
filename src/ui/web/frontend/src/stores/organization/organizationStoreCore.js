/**
 * Organization Store Core
 *
 * S-Grade: Main organization store.
 * Single responsibility: Compose organization functionality.
 */

import { defineStore } from 'pinia'
import { createOrganizationState, createOrganizationGetters } from './state'
import { createOrgActions } from './orgActions'
import { createMemberActions, createUtilityActions } from './memberActions'

export const useOrganizationStore = defineStore('organization', () => {
  // Create state
  const state = createOrganizationState()

  // Create getters
  const getters = createOrganizationGetters(state)

  // Create actions
  const orgActions = createOrgActions(state)
  const memberActions = createMemberActions(state)
  const utilityActions = createUtilityActions(state)

  return {
    // State
    ...state,

    // Getters
    ...getters,

    // Actions
    ...orgActions,
    ...memberActions,
    ...utilityActions,
  }
})
