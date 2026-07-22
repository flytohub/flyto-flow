/**
 * Template Save Core Composable
 *
 * S-Grade: Main template save composable.
 * Single responsibility: Compose save functionality.
 */

import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { prepareSaveData } from './dataPreparation'
import { validateBeforeSave } from './validation'
import { createSaveActions } from './saveActions'
import { createNavigationActions } from './navigationActions'

/**
 * Create save composable
 * @param {Object} options
 * @param {Ref} options.elements - Workflow elements
 * @param {Ref} options.sections - UI sections
 * @param {Ref} options.templateData - Template data computed
 * @param {Ref} options.templateName - Template name
 * @param {Ref} options.existingTemplateId - Existing template ID
 * @param {Ref} options.hasUnsavedChanges - Unsaved changes flag
 * @param {Ref} options.isSaving - Saving in progress flag
 * @param {Ref} options.showSaveDialog - Save dialog visibility
 * @param {Function} options.showToast - Toast notification function
 */
export function useTemplateSave(options) {
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
    showSaveDialog,
    showToast
  } = options

  const { t } = useI18n()
  const router = useRouter()

  // Create save actions
  const saveActions = createSaveActions({
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
  })

  // Create navigation actions
  const navigationActions = createNavigationActions({
    hasUnsavedChanges,
    showSaveDialog,
    saveTemplate: saveActions.saveTemplate,
    router
  })

  // Prepare data helper
  function prepareData() {
    return prepareSaveData({ elements, sections, templateData, viewport, errorHandling, checkpoints })
  }

  // Validate helper
  async function validate() {
    return validateBeforeSave({ elements, templateData, showToast, t })
  }

  return {
    prepareSaveData: prepareData,
    validateBeforeSave: validate,
    saveTemplate: saveActions.saveTemplate,
    saveAsNewTemplate: saveActions.saveAsNewTemplate,
    autoSave: saveActions.autoSave,
    handleBack: navigationActions.handleBack,
    leaveWithoutSaving: navigationActions.leaveWithoutSaving,
    saveAndLeave: navigationActions.saveAndLeave
  }
}
