/**
 * Modules Store
 * Manages module catalog state for the workflow builder
 *
 * Design: Backend is single source of truth.
 * - One API call fetches ALL modules (default + expert)
 * - Frontend stores metadata and renders from schema
 * - Simple localStorage cache with TTL
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getTieredCatalog } from '@/api/modules'
import { telemetry } from '@/services/telemetry'
import { normalizeTieredCatalogResponse } from '@/utils/dataBoundary'

const CACHE_KEY = 'flyto_modules_cache'
// Dev: 2 min cache (fast iteration), Prod: 30 min (minimize API calls)
const CACHE_TTL_MS = import.meta.env.DEV ? 2 * 60 * 1000 : 30 * 60 * 1000

export const useModulesStore = defineStore('modules', () => {
  // ========== State ==========
  const availableSteps = ref({})
  const moduleCategories = ref([])
  const modulesMetadata = ref({})
  const defaultModulesList = ref([])
  const expertModulesList = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const hasLoaded = ref(false)

  // ========== Getters ==========
  const hasModules = computed(() => Object.keys(modulesMetadata.value).length > 0)
  const isReady = computed(() => hasLoaded.value && !isLoading.value && !error.value)

  const getModuleById = computed(() => {
    return (moduleId) => modulesMetadata.value[moduleId]
  })

  const getModulesByCategory = computed(() => {
    return (category) => availableSteps.value[category] || []
  })

  // ========== Cache ==========
  function loadFromCache(locale) {
    try {
      const raw = localStorage.getItem(CACHE_KEY)
      if (!raw) return null
      const cached = JSON.parse(raw)
      if (!cached?.timestamp) return null
      if (cached.locale !== locale) return null
      if (Date.now() - cached.timestamp > CACHE_TTL_MS) return null
      // Must have real data (not stale partial cache)
      const metaCount = cached.modulesMetadata ? Object.keys(cached.modulesMetadata).length : 0
      if (metaCount < 50) return null
      // Must have new cache format (defaultModules array, not old default.modules)
      if (!Array.isArray(cached.defaultModules)) return null
      return cached
    } catch {
      return null
    }
  }

  function saveToCache(locale, data, version) {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify({
        locale,
        timestamp: Date.now(),
        version,
        ...data
      }))
    } catch {
      // quota exceeded — ignore
    }
  }

  function hydrateStore(data) {
    const normalized = normalizeTieredCatalogResponse(data)
    defaultModulesList.value = normalized.defaultModules
    expertModulesList.value = normalized.expertModules
    availableSteps.value = normalized.modulesByCategory
    moduleCategories.value = normalized.moduleCategories
    modulesMetadata.value = normalized.modulesMetadata
    hasLoaded.value = true
  }

  // ========== Actions ==========
  /**
   * Load all modules from backend.
   * Always fetches default + expert in one call.
   *
   * @param {string} locale - Locale for translations
   * @param {Object} options
   * @param {boolean} options.forceRefresh - Bypass cache
   * @param {string} options.excludeTemplateId - Template ID to exclude (prevent self-reference)
   */
  async function loadModules(locale = 'en', options = {}) {
    const { forceRefresh = false, excludeTemplateId = null } = options

    if (isLoading.value) return { ok: true }

    // Try cache first (even with excludeTemplateId — filter client-side)
    if (!forceRefresh) {
      const cached = loadFromCache(locale)
      if (cached) {
        hydrateStore(cached)
        if (excludeTemplateId) {
          _filterExcludedTemplate(excludeTemplateId)
        }
        telemetry.track('modules.cache_hit', {
          count: Object.keys(modulesMetadata.value).length,
          cacheAge: Date.now() - cached.timestamp
        })
        return { ok: true, fromCache: true }
      }
    }

    isLoading.value = true
    error.value = null

    try {
      const lang = locale?.split('-')[0] || 'en'

      const response = await getTieredCatalog({
        lang,
        includeExpert: true,
        includeTemplates: true,
        forceRefresh,
        excludeTemplateId
      })

      const storeData = normalizeTieredCatalogResponse(response)

      hydrateStore(storeData)

      saveToCache(locale, storeData, response.version)

      telemetry.track('modules.catalog_load', {
        totalModules: Object.keys(modulesMetadata.value).length,
        defaultCount: defaultModulesList.value.length,
        expertCount: expertModulesList.value.length,
        categoriesCount: moduleCategories.value.length
      })

      return { ok: true }
    } catch (err) {
      error.value = err.message || 'Failed to load modules'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  function _filterExcludedTemplate(templateId) {
    // Remove from metadata
    for (const [key, mod] of Object.entries(modulesMetadata.value)) {
      const sourceData = mod.sourceData || {}
      if (sourceData.templateId === templateId || sourceData.libraryId === templateId) {
        delete modulesMetadata.value[key]
      }
    }
    // Remove from default modules list
    defaultModulesList.value = defaultModulesList.value.filter(mod => {
      const sourceData = mod.sourceData || {}
      return sourceData.templateId !== templateId && sourceData.libraryId !== templateId
    })
  }

  function clearCache() {
    try { localStorage.removeItem(CACHE_KEY) } catch { /* ignore */ }
  }

  function reset() {
    availableSteps.value = {}
    moduleCategories.value = []
    modulesMetadata.value = {}
    defaultModulesList.value = []
    expertModulesList.value = []
    isLoading.value = false
    error.value = null
    hasLoaded.value = false
  }

  return {
    // State
    availableSteps,
    moduleCategories,
    modulesMetadata,
    defaultModulesList,
    expertModulesList,
    isLoading,
    error,
    hasLoaded,
    isReady,

    // Getters
    hasModules,
    getModuleById,
    getModulesByCategory,

    // Actions
    loadModules,
    reset,
    clearCache
  }
})
