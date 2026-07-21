/**
 * Plugin Store Core
 *
 * S-Grade: Main plugin store.
 * Single responsibility: Compose plugin functionality.
 */

import { defineStore } from 'pinia'
import { createPluginState, createPluginGetters } from './state'
import { createSearchActions } from './searchActions'
import { createInstallActions } from './installActions'
import { createUtilityActions } from './utilityActions'

export const usePluginStore = defineStore('plugin', () => {
  // Create state
  const state = createPluginState()

  // Create getters
  const getters = createPluginGetters(state)

  // Create actions
  const searchActions = createSearchActions(state)
  const installActions = createInstallActions(state)
  const utilityActions = createUtilityActions(state)

  return {
    // State
    ...state,

    // Getters
    ...getters,

    // Actions
    ...searchActions,
    ...installActions,
    ...utilityActions,
  }
})
