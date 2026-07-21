/**
 * Node Styles Composable
 *
 * All module metadata (icon, color, label) comes from flyto-core via modulesStore.
 * Custom appearances (admin-set icons/colors) are merged into modulesMetadata.
 * This composable provides helper functions to access that data.
 *
 * Design: Backend is single source of truth.
 * - Icon: Backend returns object format { type: "lucide"|"url", name?, url? }
 * - Color: Backend already merged, frontend just reads
 * - Label: Backend returns pre-translated label
 */

import { useI18n } from 'vue-i18n'
import * as LucideIcons from 'lucide-vue-next'
import { useModulesStore } from '@/stores/modulesStore'
import { getBaseModuleType } from '@/utils/moduleIdUtils'

const { Box, Loader2, CircleCheck, XCircle, Clock, Play } = LucideIcons

// Default fallback values
const DEFAULT_COLOR = '#6C757D'
const DEFAULT_GRADIENT = 'linear-gradient(135deg, #6C757D 0%, #868E96 100%)'

// Status icons (UI-only, not from core)
const STATUS_ICONS = {
  running: Loader2,
  success: CircleCheck,
  error: XCircle,
  pending: Clock
}

export function useNodeStyles() {
  const { t, te } = useI18n()
  const modulesStore = useModulesStore()

  /**
   * Get category from module ID
   */
  function getCategory(moduleId) {
    if (!moduleId) return 'default'
    const metadata = modulesStore.modulesMetadata[moduleId]
    return metadata?.category || moduleId.split('.')[0] || 'default'
  }

  /**
   * Get module color from store
   */
  function getCategoryColor(moduleId) {
    const metadata = modulesStore.modulesMetadata[moduleId]
    return metadata?.color || DEFAULT_COLOR
  }

  /**
   * Get module gradient based on color
   */
  function getGradient(moduleId) {
    const color = getCategoryColor(moduleId)
    return `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`
  }

  /**
   * Alias for backward compatibility
   */
  function getCategoryColors(moduleId) {
    const color = getCategoryColor(moduleId)
    return { color, gradient: getGradient(moduleId) }
  }

  /**
   * Get category label (i18n or fallback)
   */
  function getCategoryLabel(moduleId) {
    const category = getCategory(moduleId)
    const translationKey = `workflowNode.categories.${category}`
    if (te(translationKey)) return t(translationKey)
    return category.charAt(0).toUpperCase() + category.slice(1)
  }

  /**
   * Get module icon from store
   *
   * Backend is single source of truth.
   * Backend always returns icon as object: { type: "lucide"|"url", name?, url? }
   * Frontend just renders - no format detection needed.
   *
   * @param {string} moduleId - Module ID
   * @returns {Component|Object} Vue component or { type: 'url', url: string }
   */
  function getNodeIcon(moduleId) {
    const metadata = modulesStore.modulesMetadata[moduleId]
    if (!metadata) return Box

    const icon = metadata.icon
    if (!icon) return Box

    // Backend returns object format: { type, value }
    // Also supports old format with name/url for backward compatibility
    if (typeof icon === 'object' && icon.type) {
      if (icon.type === 'url') {
        const url = icon.value || icon.url
        return { type: 'url', url: url }
      }
      // Lucide icon - lookup by name
      if (icon.type === 'lucide') {
        const name = icon.value || icon.name || 'Package'
        return LucideIcons[name] || Box
      }
    }

    // Fallback for pre-loaded Vue components (rare edge case)
    if (typeof icon !== 'string') {
      return icon
    }

    // Final fallback
    return Box
  }

  /**
   * Check if icon is a custom URL icon
   */
  function isCustomUrlIcon(icon) {
    return icon && typeof icon === 'object' && icon.type === 'url'
  }

  /**
   * Get module label from store.
   * Backend returns pre-translated labels — just render.
   *
   * @param {string} moduleId - Module ID
   * @param {Object} options - Optional options
   * @param {string} options.overrideLabel - Explicit label to use
   * @param {Object} options.metadata - Pre-fetched metadata (optional)
   * @returns {string} Localized label
   */
  function getNodeLabel(moduleId, options = {}) {
    const { overrideLabel, metadata: providedMetadata } = options

    if (overrideLabel) return overrideLabel
    if (!moduleId) return t('workflowNode.defaultNodeLabel')

    const metadata = providedMetadata || modulesStore.modulesMetadata[moduleId]

    if (metadata?.label) {
      return metadata.label
    }

    return moduleId.split('.').pop()
  }

  /**
   * Get node subtitle from params
   */
  function getNodeSubtitle(data) {
    if (data.params?.variableName) return `$${data.params.variableName}`
    if (data.params?.url) return truncate(data.params.url, 25)
    if (data.params?.selector) return truncate(data.params.selector, 25)
    if (data.params?.label) return data.params.label
    return data.module || ''
  }

  function truncate(str, len) {
    if (!str) return ''
    return str.length > len ? str.substring(0, len - 2) + '...' : str
  }

  function getStatusIcon(status) {
    return STATUS_ICONS[status] || Play
  }

  return {
    getCategory,
    getCategoryColor,
    getCategoryColors,
    getGradient,
    getCategoryLabel,
    getNodeIcon,
    isCustomUrlIcon,
    getNodeLabel,
    getNodeSubtitle,
    getStatusIcon,
    truncate,
    // Constants for backward compatibility
    CATEGORY_COLORS: {},
    ICON_MAP: {}
  }
}
