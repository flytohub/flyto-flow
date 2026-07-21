/**
 * Template Store
 * Manages template state and operations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { templatesAPI } from '@/api/templates'
import i18n from '@/i18n'
import { trackTemplate } from '@/utils/telemetryTracker'
import { asObject, normalizeTemplateListResponse } from '@/utils/dataBoundary'

export const useTemplateStore = defineStore('template', () => {
  // ========== State ==========
  const templates = ref([])
  const currentTemplate = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const hasLoaded = ref(false)

  // ========== S-Grade: Backend-computed counts ==========
  const enabledCount = ref(0)
  const totalCount = ref(0)

  // ========== Getters ==========
  const hasTemplates = computed(() => templates.value.length > 0)
  const isReady = computed(() => hasLoaded.value && !isLoading.value && !error.value)

  const getTemplateById = computed(() => {
    return (id) => templates.value.find(t => t?.id === id)
  })

  // ========== Actions ==========

  /**
   * Fetch templates list
   *
   * S-Grade: Uses backend-computed counts when available.
   *
   * @param {Object} options - Query options
   * @param {boolean} options.enabled - Filter by enabled status
   */
  async function fetchTemplates(options = {}) {
    isLoading.value = true
    error.value = null

    try {
      const result = await templatesAPI.listTemplates(options)
      const normalized = normalizeTemplateListResponse(result)

      templates.value = normalized.templates
      enabledCount.value = normalized.enabledCount
      totalCount.value = normalized.totalCount

      if (!normalized.ok) {
        error.value = normalized.error || i18n.global.t('error.failedToLoadTemplates')
      }
      hasLoaded.value = true
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToLoadTemplates')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTemplateById(id) {
    isLoading.value = true
    error.value = null

    try {
      const data = await templatesAPI.getById(id)
      currentTemplate.value = Object.keys(asObject(data)).length > 0 ? asObject(data) : null
      hasLoaded.value = true
      return currentTemplate.value
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToLoadTemplate')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createTemplate(templateData) {
    isLoading.value = true
    error.value = null

    try {
      const data = await templatesAPI.create(templateData)
      const template = asObject(data)
      if (Object.keys(template).length > 0) {
        templates.value.push(template)
      }
      currentTemplate.value = Object.keys(template).length > 0 ? template : null

      // Track template create event
      trackTemplate.create(template.id, { name: template.name })

      hasLoaded.value = true
      return template
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToCreateTemplate')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateTemplate(id, templateData) {
    isLoading.value = true
    error.value = null

    try {
      const data = await templatesAPI.update(id, templateData)
      const template = asObject(data)
      const index = templates.value.findIndex(t => t?.id === id)
      if (index !== -1) {
        templates.value[index] = template
      }
      if (currentTemplate.value?.id === id) {
        currentTemplate.value = template
      }

      // Track template save event
      trackTemplate.save(id)

      hasLoaded.value = true
      return template
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUpdateTemplate')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteTemplate(id) {
    isLoading.value = true
    error.value = null

    try {
      await templatesAPI.delete(id)
      templates.value = templates.value.filter(t => t?.id !== id)
      if (currentTemplate.value?.id === id) {
        currentTemplate.value = null
      }

      // Track template delete event
      trackTemplate.delete(id)
      hasLoaded.value = true
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToDeleteWorkflow')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function setCurrentTemplate(template) {
    currentTemplate.value = template
  }

  function clearError() {
    error.value = null
  }

  function reset() {
    templates.value = []
    currentTemplate.value = null
    isLoading.value = false
    error.value = null
    hasLoaded.value = false
    // S-Grade: Reset backend-computed counts
    enabledCount.value = 0
    totalCount.value = 0
  }

  return {
    templates,
    currentTemplate,
    isLoading,
    error,
    hasLoaded,
    isReady,
    // S-Grade: Backend-computed counts
    enabledCount,
    totalCount,
    hasTemplates,
    getTemplateById,
    fetchTemplates,
    fetchTemplateById,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    setCurrentTemplate,
    clearError,
    reset
  }
})
