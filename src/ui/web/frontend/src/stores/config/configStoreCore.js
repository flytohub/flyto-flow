/**
 * Config Store Core
 *
 * S-Grade: Main config store.
 * Single responsibility: Compose config functionality.
 *
 * All configuration comes from backend /config/all endpoint.
 * DEFAULTS are fallbacks only.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { DEFAULTS } from './defaults'
import { createConfigGetters } from './getters'
import { createConfigActions } from './actions'

export const useConfigStore = defineStore('config', () => {
  // ========== Core State ==========
  const timing = ref(DEFAULTS.timing)
  const layout = ref(DEFAULTS.layout)
  const theme = ref(DEFAULTS.theme)
  const limits = ref(DEFAULTS.limits)
  const shortcuts = ref(DEFAULTS.shortcuts)

  // ========== Module Configuration State ==========
  const llm = ref(DEFAULTS.llm)
  const triggers = ref(DEFAULTS.triggers)
  const http = ref(DEFAULTS.http)
  const paramTypes = ref(DEFAULTS.paramTypes)
  const outputTypes = ref(DEFAULTS.outputTypes)

  // ========== Marketplace State ==========
  const marketplace = ref(DEFAULTS.marketplace)
  const subscription = ref(DEFAULTS.subscription)

  // ========== Workflow Types State ==========
  const workflowTypes = ref(DEFAULTS.workflowTypes)
  const formTypes = ref(DEFAULTS.formTypes)

  // ========== Misc State ==========
  const countries = ref(DEFAULTS.countries)
  const quickStart = ref(DEFAULTS.quickStart)
  const messaging = ref(DEFAULTS.messaging)
  const breakpoints = ref(DEFAULTS.breakpoints)
  const nodeDesign = ref(DEFAULTS.nodeDesign)

  // ========== Loading State ==========
  const isLoaded = ref(false)
  const isLoading = ref(false)
  const error = ref(null)

  // Create state object for factories
  const state = {
    // Core
    timing,
    layout,
    theme,
    limits,
    shortcuts,
    // Module config
    llm,
    triggers,
    http,
    paramTypes,
    outputTypes,
    // Marketplace
    marketplace,
    subscription,
    // Workflow
    workflowTypes,
    formTypes,
    // Misc
    countries,
    quickStart,
    messaging,
    breakpoints,
    nodeDesign,
    // Loading
    isLoaded,
    isLoading,
    error,
  }

  // Create getters
  const getters = createConfigGetters(state)

  // Create actions
  const actions = createConfigActions(state)

  return {
    // Core State
    timing,
    layout,
    theme,
    limits,
    shortcuts,

    // Module Configuration State
    llm,
    triggers,
    http,
    paramTypes,
    outputTypes,

    // Marketplace State
    marketplace,
    subscription,

    // Workflow Types State
    workflowTypes,
    formTypes,

    // Misc State
    countries,
    quickStart,
    messaging,
    breakpoints,
    nodeDesign,

    // Loading State
    isLoaded,
    isLoading,
    error,

    // Getters
    ...getters,

    // Actions
    ...actions,
  }
})
