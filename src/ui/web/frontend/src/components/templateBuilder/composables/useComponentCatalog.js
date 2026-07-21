import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import * as icons from 'lucide-vue-next'
import {
  COMPONENT_TYPES,
  getComponentList,
  getCategoryList,
  getComponentsByCategory,
  getComponentConfig
} from '../_config/componentRegistry'

/**
 * Composable for managing the component catalog
 * Uses componentRegistry as the single source of truth
 */
export function useComponentCatalog() {
  const { t } = useI18n()

  function resolveIcon(iconName) {
    return icons[iconName] || icons.CircleDot
  }

  const availableComponents = computed(() =>
    getComponentList().map(comp => ({
      type: comp.type,
      label: t(comp.labelKey),
      icon: resolveIcon(comp.icon),
      category: t(`templateBuilder.categories.${comp.category.replace('-', '')}`) || comp.category
    }))
  )

  const componentCategories = computed(() => {
    const allCategory = t('templateBuilder.categories.all')
    const categories = getCategoryList().map(c => t(c.labelKey))
    return [allCategory, ...categories]
  })

  function filterComponents(searchQuery, selectedCategory) {
    let result = availableComponents.value
    const allCategory = t('templateBuilder.categories.all')

    if (selectedCategory && selectedCategory !== allCategory) {
      result = result.filter(c => c.category === selectedCategory)
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(c =>
        c.label.toLowerCase().includes(query) ||
        c.type.toLowerCase().includes(query) ||
        c.category.toLowerCase().includes(query)
      )
    }

    return result
  }

  function getComponentByType(type) {
    const config = getComponentConfig(type)
    if (!config) return null
    return {
      type: config.type,
      label: t(config.labelKey),
      icon: resolveIcon(config.icon),
      category: config.category
    }
  }

  function getComponentIcon(type) {
    const config = getComponentConfig(type)
    return config ? resolveIcon(config.icon) : null
  }

  return {
    availableComponents,
    componentCategories,
    filterComponents,
    getComponentByType,
    getComponentIcon
  }
}
