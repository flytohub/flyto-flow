/**
 * Save Actions
 *
 * S-Grade: Template save operations.
 * Single responsibility: Execute save operations.
 *
 * Note: prepareSaveData is now async to ensure backend conversion.
 * ConversionError is handled with user-friendly messages.
 */

import { templatesAPI } from '../../../api/templates'
import { DEFAULTS } from '@/config/defaults'
import { prepareSaveData } from './dataPreparation'
import { validateBeforeSave } from './validation'
import { ConversionError, ConversionErrorCodes } from '../../../utils/converter'

/**
 * Create save action handlers
 * @param {Object} options - All required refs and functions
 * @returns {Object} Save action functions
 */
export function createSaveActions(options) {
  const {
    elements,
    sections,
    templateData,
    templateName,
    existingTemplateId,
    viewport,
    errorHandling,
    checkpoints,
    hasUnsavedChanges,
    isSaving,
    showToast,
    t
  } = options

  /**
   * Save template - creates new or updates existing
   * @returns {Promise<{ok: boolean, error?: string}>}
   */
  async function saveTemplate() {
    if (isSaving.value) return { ok: false, error: 'already_saving' }
    const validationResult = await validateBeforeSave({ elements, templateData, showToast, t })
    if (!validationResult.valid) return { ok: false, error: 'validation_failed' }

    isSaving.value = true

    try {
      const saveData = await prepareSaveData({ elements, sections, templateData, viewport, errorHandling, checkpoints })

      if (existingTemplateId.value) {
        const result = await templatesAPI.updateTemplate(existingTemplateId.value, saveData)
        if (!result.ok) {
          throw new Error(result.error || t('templateBuilder.messages.updateFailed'))
        }
        showToast(t('templateBuilder.alerts.templateUpdatedSuccess', { name: saveData.name }), 'success')
      } else {
        const result = await templatesAPI.createTemplate(saveData)
        if (!result.ok || !result.template) {
          throw new Error(result.error || t('templateBuilder.messages.createFailed'))
        }
        existingTemplateId.value = result.template.id
        showToast(t('templateBuilder.alerts.templateSavedSuccess', { id: result.template.id, name: result.template.name || saveData.name }), 'success')

        // Invalidate modules cache so new template appears in catalog
        try {
          const { useModulesStore } = await import('@/stores/modulesStore')
          useModulesStore().clearCache()
        } catch (err) { console.warn('[saveActions] cache clear:', err) }
      }

      hasUnsavedChanges.value = false
      return { ok: true }
    } catch (error) {
      // Handle ConversionError with specific user-friendly messages
      if (error instanceof ConversionError) {
        const errorKey = error.code === ConversionErrorCodes.BACKEND_UNAVAILABLE
          ? 'templateBuilder.alerts.connectionError'
          : 'templateBuilder.alerts.conversionError'
        const errorMessage = t(errorKey, error.message)
        showToast(errorMessage, 'error', DEFAULTS.TIMING.TOAST_DURATION_ERROR)
        return { ok: false, error: error.code, details: error.details }
      }

      const errorMessage = error.response?.data?.detail || error.message || t('common.unknownError')
      showToast(t('templateBuilder.alerts.templateSaveFailed', { error: errorMessage }), 'error', DEFAULTS.TIMING.TOAST_DURATION_ERROR)
      return { ok: false, error: errorMessage }
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Auto-save template silently
   */
  async function autoSave() {
    if (!existingTemplateId.value) return { ok: false, reason: 'no_existing_template' }
    if (isSaving.value) return { ok: false, reason: 'already_saving' }
    if (!templateData.value.name || !templateData.value.name.trim()) {
      return { ok: false, reason: 'no_name' }
    }

    isSaving.value = true

    try {
      const saveData = await prepareSaveData({ elements, sections, templateData, viewport, errorHandling, checkpoints })

      const result = await templatesAPI.updateTemplate(existingTemplateId.value, saveData)
      if (!result.ok) {
        return { ok: false, reason: result.error }
      }

      hasUnsavedChanges.value = false
      return { ok: true }
    } catch (error) {
      // ConversionError in auto-save: log but don't show toast (silent)
      if (error instanceof ConversionError) {
        return { ok: false, reason: error.code, details: error.details }
      }
      return { ok: false, reason: error.message }
    } finally {
      isSaving.value = false
    }
  }

  /**
   * Save a local copy as a new workflow.
   * @returns {Promise<{ok: boolean, error?: string}>}
   */
  async function saveAsNewTemplate() {
    if (isSaving.value) return { ok: false, error: 'already_saving' }
    const validationResult = await validateBeforeSave({ elements, templateData, showToast, t })
    if (!validationResult.valid) return { ok: false, error: 'validation_failed' }

    isSaving.value = true

    try {
      const saveData = await prepareSaveData({ elements, sections, templateData, viewport, errorHandling, checkpoints })
      saveData.name = `${saveData.name} (Copy)`

      const result = await templatesAPI.createTemplate(saveData)
      if (!result.ok || !result.template) {
        throw new Error(result.error || t('templateBuilder.messages.createFailed'))
      }
      existingTemplateId.value = result.template.id
      templateName.value = result.template.name || saveData.name
      showToast(t('templateBuilder.alerts.templateSavedSuccess', { id: result.template.id, name: result.template.name || saveData.name }), 'success')

      // Invalidate modules cache so new template appears in catalog
      try {
        const { useModulesStore } = await import('@/stores/modulesStore')
        useModulesStore().clearCache()
      } catch (err) { console.warn('[saveActions] cache clear:', err) }

      hasUnsavedChanges.value = false
      return { ok: true }
    } catch (error) {
      // Handle ConversionError with specific user-friendly messages
      if (error instanceof ConversionError) {
        const errorKey = error.code === ConversionErrorCodes.BACKEND_UNAVAILABLE
          ? 'templateBuilder.alerts.connectionError'
          : 'templateBuilder.alerts.conversionError'
        const errorMessage = t(errorKey, error.message)
        showToast(errorMessage, 'error', DEFAULTS.TIMING.TOAST_DURATION_ERROR)
        return { ok: false, error: error.code, details: error.details }
      }

      const errorMessage = error.response?.data?.detail || error.message || t('common.unknownError')
      showToast(t('templateBuilder.alerts.templateSaveFailed', { error: errorMessage }), 'error', DEFAULTS.TIMING.TOAST_DURATION_ERROR)
      return { ok: false, error: errorMessage }
    } finally {
      isSaving.value = false
    }
  }

  return {
    saveTemplate,
    autoSave,
    saveAsNewTemplate
  }
}
