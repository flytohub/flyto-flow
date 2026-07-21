/**
 * Plugin Store State
 *
 * S-Grade: State refs and getters.
 * Single responsibility: Plugin state management.
 */

import { ref, computed } from 'vue'

/**
 * Create plugin store state
 * @returns {Object} State refs
 */
export function createPluginState() {
  const searchResults = ref([])
  const installedPlugins = ref([])
  const selectedPlugin = ref(null)
  const cacheStats = ref(null)
  const isLoading = ref(false)
  const isInstalling = ref(false)
  const error = ref(null)

  return {
    searchResults,
    installedPlugins,
    selectedPlugin,
    cacheStats,
    isLoading,
    isInstalling,
    error,
  }
}

/**
 * Create plugin store getters
 * @param {Object} state - State refs
 * @returns {Object} Computed getters
 */
export function createPluginGetters(state) {
  const { searchResults, installedPlugins } = state

  const hasInstalled = computed(() => installedPlugins.value.length > 0)
  const hasSearchResults = computed(() => searchResults.value.length > 0)
  const installedCount = computed(() => installedPlugins.value.length)

  /**
   * Check if a model is installed
   */
  function isInstalled(modelId) {
    return installedPlugins.value.some(p => p.id === modelId || p.modelId === modelId)
  }

  return {
    hasInstalled,
    hasSearchResults,
    installedCount,
    isInstalled,
  }
}
