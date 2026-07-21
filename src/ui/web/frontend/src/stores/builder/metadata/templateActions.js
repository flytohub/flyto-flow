/**
 * Template Actions
 *
 * S-Grade: Template metadata operations.
 * Single responsibility: Load, reset, update template metadata.
 */

/**
 * Create template actions
 * @param {Object} state - State refs
 * @returns {Object} Template action functions
 */
import { normalizeTemplatePayload } from '@/utils/dataBoundary'

export function createTemplateActions(state) {
  const {
    templateName,
    templateId,
    templateDescription,
    existingTemplateId,
    templateCreatorId,
    templateMutability,
    templateVisibility,
    templateListed,
    isWorkflowVisible,
    sections,
    hasUnsavedChanges,
    isLoading,
    loadError,
    counters
  } = state

  function setTemplateName(name) {
    templateName.value = name
    hasUnsavedChanges.value = true
  }

  function setTemplateDescription(desc) {
    templateDescription.value = desc
    hasUnsavedChanges.value = true
  }

  function loadTemplate(template) {
    isLoading.value = true
    loadError.value = null

    try {
      const normalized = normalizeTemplatePayload(template)
      existingTemplateId.value = normalized.id || null
      templateName.value = normalized.templateName
      templateId.value = normalized.templateId
      templateDescription.value = normalized.templateDescription
      templateCreatorId.value = normalized.creatorId
      templateMutability.value = normalized.mutability
      templateVisibility.value = normalized.visibility
      templateListed.value = normalized.listed
      isWorkflowVisible.value = normalized.isWorkflowVisible
      sections.value = normalized.sections

      if (!normalized.id) {
        loadError.value = 'Invalid template payload'
      }

      hasUnsavedChanges.value = false
    } catch (error) {
      loadError.value = error.message
    } finally {
      isLoading.value = false
    }
  }

  function resetTemplate() {
    templateName.value = ''
    templateId.value = 'new_template'
    templateDescription.value = ''
    existingTemplateId.value = null
    templateCreatorId.value = null
    templateMutability.value = 'fork_on_use'
    templateVisibility.value = 'private'
    templateListed.value = false
    isWorkflowVisible.value = true  // New templates always have visible workflow
    sections.value = []
    hasUnsavedChanges.value = false
    loadError.value = null
    counters.section = 1
    counters.component = 1
  }

  return {
    setTemplateName,
    setTemplateDescription,
    loadTemplate,
    resetTemplate,
  }
}
