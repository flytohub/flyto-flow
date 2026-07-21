/**
 * Tab History Management
 *
 * S-Grade: History tracking for tab navigation.
 * Single responsibility: Manage navigation history.
 */

import { ref } from 'vue'

/** Maximum history entries to keep */
const MAX_HISTORY_SIZE = 20

/**
 * Create tab history manager
 * @param {string} initialTabId - Initial tab ID to add to history
 * @returns {Object} History management utilities
 */
export function useTabHistory(initialTabId = null) {
  const history = ref([])

  /**
   * Initialize history with a tab ID
   * @param {string} tabId - Tab ID
   */
  function initialize(tabId) {
    history.value = tabId ? [tabId] : []
  }

  /**
   * Add tab to history
   * @param {string} tabId - Tab ID to add
   */
  function addToHistory(tabId) {
    // Remove if already exists
    history.value = history.value.filter(id => id !== tabId)
    // Add to end
    history.value.push(tabId)
    // Limit history size
    if (history.value.length > MAX_HISTORY_SIZE) {
      history.value.shift()
    }
  }

  /**
   * Remove tab from history
   * @param {string} tabId - Tab ID to remove
   */
  function removeFromHistory(tabId) {
    history.value = history.value.filter(id => id !== tabId)
  }

  /**
   * Get last tab in history
   * @returns {string|null} Last tab ID or null
   */
  function getLastTab() {
    return history.value[history.value.length - 1] || null
  }

  /**
   * Clear history
   */
  function clear() {
    history.value = []
  }

  // Initialize if provided
  if (initialTabId) {
    initialize(initialTabId)
  }

  return {
    history,
    initialize,
    addToHistory,
    removeFromHistory,
    getLastTab,
    clear
  }
}
