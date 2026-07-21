/**
 * Tab Operations
 *
 * S-Grade: Tab CRUD and state modification operations.
 * Single responsibility: Tab state mutations.
 */

/**
 * Find child tabs of a given tab
 * @param {string} tabId - Parent tab ID
 * @param {Array} allTabs - All tabs
 * @param {Function} getParentFlowId - Parent flow ID resolver
 * @returns {Array} Child tabs
 */
export function findChildTabs(tabId, allTabs, getParentFlowId) {
  return allTabs.filter(t =>
    t.parentNodeId && allTabs.find(p =>
      p.id === tabId && p.flowId === getParentFlowId(t.parentNodeId)
    )
  )
}

/**
 * Check if tab can be closed
 * @param {Object} tab - Tab to check
 * @returns {Object} { canClose, reason }
 */
export function canCloseTab(tab) {
  if (!tab) {
    return { canClose: false, reason: 'Tab not found' }
  }
  if (tab.depth === 0) {
    return { canClose: false, reason: 'Cannot close root tab' }
  }
  if (tab.isDirty) {
    return { canClose: false, reason: 'Tab has unsaved changes' }
  }
  return { canClose: true, reason: null }
}

/**
 * Create tab state mutators
 * @param {Ref} tabsRef - Tabs array ref
 * @returns {Object} Mutator functions
 */
export function createTabMutators(tabsRef) {
  return {
    /**
     * Set dirty state on a tab
     * @param {string} tabId - Tab ID
     * @param {boolean} isDirty - Dirty state
     */
    setDirty(tabId, isDirty = true) {
      const tab = tabsRef.value.find(t => t.id === tabId)
      if (tab) {
        tab.isDirty = isDirty
      }
    },

    /**
     * Update tab label
     * @param {string} tabId - Tab ID
     * @param {string} label - New label
     */
    updateLabel(tabId, label) {
      const tab = tabsRef.value.find(t => t.id === tabId)
      if (tab) {
        tab.label = label
      }
    },

    /**
     * Get tab by flow ID
     * @param {string} flowId - Flow ID
     * @returns {Object|null} Tab or null
     */
    getTabByFlowId(flowId) {
      return tabsRef.value.find(t => t.flowId === flowId) || null
    },

    /**
     * Check if subflow is open
     * @param {string} flowId - Flow ID
     * @returns {boolean} Whether subflow tab is open
     */
    isSubflowOpen(flowId) {
      return tabsRef.value.some(t => t.flowId === flowId)
    },

    /**
     * Get tabs at a specific depth
     * @param {number} depth - Nesting depth
     * @returns {Array} Tabs at depth
     */
    getTabsAtDepth(depth) {
      return tabsRef.value.filter(t => t.depth === depth)
    },

    /**
     * Add a tab
     * @param {Object} tab - Tab to add
     */
    addTab(tab) {
      tabsRef.value.push(tab)
    },

    /**
     * Remove a tab by ID
     * @param {string} tabId - Tab ID
     * @returns {boolean} Whether removed
     */
    removeTab(tabId) {
      const index = tabsRef.value.findIndex(t => t.id === tabId)
      if (index > -1) {
        tabsRef.value.splice(index, 1)
        return true
      }
      return false
    }
  }
}
