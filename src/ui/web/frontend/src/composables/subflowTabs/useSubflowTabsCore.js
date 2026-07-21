/**
 * Subflow Tabs Core Composable
 *
 * S-Grade: Main subflow tab management composable.
 * Uses extracted helpers for breadcrumbs, history, operations, and types.
 */

import { ref, computed } from 'vue'
import { createRootTab, createSubflowTab } from './types'
import { buildBreadcrumbs, findParentFlowId } from './breadcrumbUtils'
import { useTabHistory } from './useTabHistory'
import { findChildTabs, canCloseTab, createTabMutators } from './tabOperations'

/**
 * useSubflowTabs composable
 * @param {Object} options - Options
 * @param {string} options.rootFlowId - Root workflow ID
 * @param {string} options.rootFlowName - Root workflow display name
 * @returns {Object} Subflow tab utilities
 */
export function useSubflowTabs(options = {}) {
  const { rootFlowId = 'root', rootFlowName = 'Main Flow' } = options

  // Tab state
  const tabs = ref([])
  const activeTabId = ref(null)
  const rootTab = createRootTab(rootFlowId, rootFlowName)

  // History management
  const { history: tabHistory, addToHistory, removeFromHistory, getLastTab } = useTabHistory()

  // Tab mutators
  const mutators = createTabMutators(tabs)

  // ========== Computed ==========
  const activeTab = computed(() => tabs.value.find(t => t.id === activeTabId.value) || null)
  const currentFlowId = computed(() => activeTab.value?.flowId || rootFlowId)
  const currentDepth = computed(() => activeTab.value?.depth || 0)
  const dirtyTabs = computed(() => tabs.value.filter(t => t.isDirty))
  const hasDirtyTabs = computed(() => dirtyTabs.value.length > 0)

  const getParentFlowId = (nodeId) =>
    findParentFlowId(nodeId, tabs.value, currentDepth.value, rootFlowId)

  const breadcrumbs = computed(() =>
    buildBreadcrumbs(activeTab.value, tabs.value, rootTab, getParentFlowId)
  )

  // ========== Actions ==========
  function initialize() {
    tabs.value = [rootTab]
    activeTabId.value = rootTab.id
    tabHistory.value = [rootTab.id]
  }

  function openSubflow(opts) {
    const { flowId, label, parentNodeId, flowData = null, templateMeta = null } = opts

    // Check if tab already exists
    const existing = mutators.getTabByFlowId(flowId)
    if (existing) {
      activeTabId.value = existing.id
      addToHistory(existing.id)
      return existing.id
    }

    // Calculate depth
    const parentTab = tabs.value.find(t =>
      t.flowId === getParentFlowId(parentNodeId) || t.id === activeTabId.value
    )
    const depth = (parentTab?.depth || 0) + 1

    // Create and add new tab
    const newTab = createSubflowTab(flowId, label, parentNodeId, depth, flowData, templateMeta)
    mutators.addTab(newTab)
    activeTabId.value = newTab.id
    addToHistory(newTab.id)

    return newTab.id
  }

  function closeTab(tabId) {
    const tab = tabs.value.find(t => t.id === tabId)
    const { canClose } = canCloseTab(tab)
    if (!canClose) return false

    // Close child tabs first
    const childTabs = findChildTabs(tabId, tabs.value, getParentFlowId)
    for (const child of childTabs) {
      closeTab(child.id)
    }

    // Remove tab and history
    mutators.removeTab(tabId)
    removeFromHistory(tabId)

    // Switch to previous or root
    if (activeTabId.value === tabId) {
      const prev = getLastTab()
      activeTabId.value = (prev && tabs.value.find(t => t.id === prev))
        ? prev : rootTab.id
    }

    return true
  }

  function switchTab(tabId) {
    if (tabs.value.find(t => t.id === tabId)) {
      activeTabId.value = tabId
      addToHistory(tabId)
    }
  }

  function navigateUp() {
    const active = activeTab.value
    if (!active || active.depth === 0) return
    const parentTab = tabs.value.find(t => t.depth === active.depth - 1)
    if (parentTab) switchTab(parentTab.id)
  }

  function navigateToRoot() {
    switchTab(rootTab.id)
  }

  // Initialize on creation
  initialize()

  return {
    // State
    tabs, activeTabId, activeTab, currentFlowId, currentDepth,
    breadcrumbs, dirtyTabs, hasDirtyTabs,
    // Actions
    initialize, openSubflow, closeTab, switchTab,
    navigateUp, navigateToRoot,
    navigateToBreadcrumb: switchTab,
    // Mutators
    setDirty: mutators.setDirty,
    updateLabel: mutators.updateLabel,
    getTabByFlowId: mutators.getTabByFlowId,
    isSubflowOpen: mutators.isSubflowOpen,
    getTabsAtDepth: mutators.getTabsAtDepth
  }
}
