/**
 * Tool Storage State
 *
 * S-Grade: Shared singleton state for tool storage.
 * Single responsibility: State management.
 */

import { ref, computed, readonly } from 'vue'

// Shared state (singleton)
export const tools = ref([])
export const categories = ref([])
export const isLoading = ref(false)
export const error = ref(null)
export const isInitialized = ref(false)
export const currentTool = ref(null)

/**
 * Create readonly refs for external use
 */
export function createReadonlyRefs() {
  return {
    tools: readonly(tools),
    categories: readonly(categories),
    isLoading: readonly(isLoading),
    error: readonly(error),
    isInitialized: readonly(isInitialized),
    currentTool
  }
}

/**
 * Create computed properties for tools
 */
export function createToolComputeds() {
  const toolCount = computed(() => tools.value.length)

  const toolsByCategory = computed(() => {
    const grouped = {}
    for (const tool of tools.value) {
      const cat = tool.meta?.category || 'other'
      if (!grouped[cat]) {
        grouped[cat] = []
      }
      grouped[cat].push(tool)
    }
    return grouped
  })

  const recentTools = computed(() => {
    return [...tools.value]
      .sort((a, b) => {
        const dateA = new Date(a.updatedAt || a.createdAt || 0)
        const dateB = new Date(b.updatedAt || b.createdAt || 0)
        return dateB - dateA
      })
      .slice(0, 10)
  })

  const hasUnsavedChanges = computed(() => {
    if (!currentTool.value) return false
    return currentTool.value._dirty === true
  })

  return {
    toolCount,
    toolsByCategory,
    recentTools,
    hasUnsavedChanges
  }
}
