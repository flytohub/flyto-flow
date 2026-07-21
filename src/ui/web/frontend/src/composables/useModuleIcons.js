/**
 * Module Icons Composable
 *
 * Simplified icon handling - backend is single source of truth.
 * Backend returns icon as object: { type: "lucide"|"url", value: string }
 * Frontend just renders, no format detection needed.
 *
 * v2.0 Changes:
 * - Backend now uses unified "value" field instead of "name"/"url"
 * - Format: { type: "lucide", value: "Package" } or { type: "url", value: "https://..." }
 */
import * as LucideIcons from 'lucide-vue-next'

// Default fallback icon
const { Package } = LucideIcons

export function useModuleIcons() {
  /**
   * Get module icon - returns Vue component or URL object
   *
   * Backend is single source of truth.
   * Backend returns icon as: { type: "lucide"|"url", value: string }
   * Frontend just renders - no format detection needed.
   *
   * @param {Object} module - Module object with icon property
   * @returns {Component|Object} Vue component or { type: 'url', url: string }
   */
  function getModuleIcon(module) {
    const icon = module?.icon

    // No icon - use fallback
    if (!icon) return Package

    // Backend returns object format: { type, value }
    if (typeof icon === 'object' && icon.type) {
      if (icon.type === 'url') {
        // Use "value" (new format) or fallback to "url" (old format)
        const url = icon.value || icon.url
        return { type: 'url', url: url }
      }
      // Lucide icon - lookup by name
      if (icon.type === 'lucide') {
        // Use "value" (new format) or fallback to "name" (old format)
        const name = icon.value || icon.name || 'Package'
        return LucideIcons[name] || Package
      }
    }

    // Fallback for pre-loaded Vue components (rare edge case)
    if (typeof icon !== 'string') {
      return icon
    }

    // Final fallback
    return Package
  }

  /**
   * Check if icon result is a URL type
   */
  function isIconUrl(icon) {
    return icon && typeof icon === 'object' && icon.type === 'url'
  }

  return {
    LucideIcons,
    getModuleIcon,
    isIconUrl
  }
}
