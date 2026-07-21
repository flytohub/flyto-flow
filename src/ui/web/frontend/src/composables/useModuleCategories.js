/**
 * Module Categories Composable
 *
 * NOTE: These are FALLBACK values only.
 * Primary source of truth is flyto-core via API (modulesStore)
 */

import { Box, Package } from 'lucide-vue-next'

// Default fallback values
const DEFAULT_COLOR = '#6C757D'
const DEFAULT_GRADIENT = 'linear-gradient(135deg, #6C757D 0%, #868E96 100%)'

// Minimal fallback config (only used when API data not available)
export const CATEGORY_CONFIG = {
  default: {
    name: 'default',
    color: DEFAULT_COLOR,
    gradient: DEFAULT_GRADIENT,
    icon: Box,
    label: 'Module'
  },
  'my-templates': {
    name: 'my-templates',
    color: '#8B5CF6',
    gradient: 'linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%)',
    icon: Package,
    label: 'My Templates',
    labelKey: 'modules.category.myTemplates'
  }
}

export function useModuleCategories() {
  function getCategoryLabel(category) {
    return CATEGORY_CONFIG[category]?.label || category.charAt(0).toUpperCase() + category.slice(1)
  }

  function getCategoryColor(category) {
    return CATEGORY_CONFIG[category]?.color || DEFAULT_COLOR
  }

  function getCategoryGradient(category) {
    return CATEGORY_CONFIG[category]?.gradient || DEFAULT_GRADIENT
  }

  function getCategoryIcon(category) {
    return CATEGORY_CONFIG[category]?.icon || Box
  }

  function adjustColor(hex, percent) {
    const num = parseInt(hex.replace('#', ''), 16)
    const amt = Math.round(2.55 * percent)
    const R = Math.min(255, (num >> 16) + amt)
    const G = Math.min(255, ((num >> 8) & 0x00FF) + amt)
    const B = Math.min(255, (num & 0x0000FF) + amt)
    return `#${(0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)}`
  }

  function getAvailableCategories(modules) {
    const categories = new Set()
    modules.forEach(m => {
      const cat = m.category || m.moduleId?.split('.')[0] || 'default'
      categories.add(cat)
    })
    return Array.from(categories).map(cat => ({
      name: cat,
      label: cat.charAt(0).toUpperCase() + cat.slice(1),
      icon: Box,
      color: DEFAULT_COLOR
    }))
  }

  return {
    CATEGORY_CONFIG,
    getCategoryLabel,
    getCategoryColor,
    getCategoryGradient,
    getCategoryIcon,
    adjustColor,
    getAvailableCategories
  }
}
