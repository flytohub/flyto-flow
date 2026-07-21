/**
 * Role Store Core
 *
 * S-Grade: Main role store.
 * Single responsibility: Compose role functionality.
 */

import { defineStore } from 'pinia'
import { createRoleState, createRoleGetters } from './state'
import { createRoleActions } from './roleActions'
import { createPermissionActions, createUtilityActions } from './permissionActions'

export const useRoleStore = defineStore('roles', () => {
  // Create state
  const state = createRoleState()

  // Create getters
  const getters = createRoleGetters(state)

  // Create actions
  const roleActions = createRoleActions(state)
  const permissionActions = createPermissionActions(state)
  const utilityActions = createUtilityActions(state)

  return {
    // State
    ...state,

    // Getters
    ...getters,

    // Actions
    ...roleActions,
    ...permissionActions,
    ...utilityActions,
  }
})
