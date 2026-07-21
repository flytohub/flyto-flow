/**
 * UX-HINT ONLY — These validators provide instant feedback while the user types.
 * The backend is the authoritative source of truth for all validation rules.
 * Do NOT rely on these for security or data integrity.
 *
 * Template Validators
 * See GET /api/config/validation-rules.
 *
 * S-Grade: Template and workflow validation.
 * Single responsibility: Validate templates and workflow steps.
 */

import { createResult } from './utils'
import { validateSection } from './componentValidators'

/**
 * Validate template name
 * @param {string} name - Template name
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateTemplateName(name) {
  if (!name || typeof name !== 'string') {
    return createResult(false, 'validation.template.nameEmpty')
  }

  const trimmedName = name.trim()

  if (trimmedName.length === 0) {
    return createResult(false, 'validation.template.nameEmpty')
  }

  if (trimmedName.length > 100) {
    return createResult(false, 'validation.template.nameTooLong', { max: 100 })
  }

  return createResult(true)
}

/**
 * Validate template ID
 * @param {string} id - Template ID
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateTemplateId(id) {
  if (!id || typeof id !== 'string') {
    return createResult(false, 'validation.template.idEmpty')
  }

  // Only allow letters, numbers, underscores, hyphens
  const idRegex = /^[a-zA-Z0-9_-]+$/

  if (!idRegex.test(id)) {
    return createResult(false, 'validation.template.idInvalidChars')
  }

  if (id.length > 50) {
    return createResult(false, 'validation.template.idTooLong', { max: 50 })
  }

  return createResult(true)
}

/**
 * Validate template data structure
 * @param {Object} templateData - Template data
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateTemplateData(templateData) {
  if (!templateData) {
    return createResult(false, 'validation.template.dataEmpty')
  }

  // Validate name
  const nameResult = validateTemplateName(templateData.name)
  if (!nameResult.valid) {
    return nameResult
  }

  // Validate ID
  const idResult = validateTemplateId(templateData.template_id)
  if (!idResult.valid) {
    return idResult
  }

  // Validate UI structure
  if (!templateData.ui) {
    return createResult(false, 'validation.template.uiRequired')
  }

  if (!Array.isArray(templateData.ui.sections)) {
    return createResult(false, 'validation.template.sectionsRequired')
  }

  // Validate each section
  for (let i = 0; i < templateData.ui.sections.length; i++) {
    const sectionResult = validateSection(templateData.ui.sections[i])
    if (!sectionResult.valid) {
      return createResult(false, 'validation.template.sectionInvalid', {
        index: i,
        error: sectionResult.errorKey
      })
    }
  }

  return createResult(true)
}

/**
 * Validate workflow step
 * @param {Object} step - Workflow step
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateWorkflowStep(step) {
  if (!step) {
    return createResult(false, 'validation.workflow.stepEmpty')
  }

  if (!step.id) {
    return createResult(false, 'validation.workflow.stepIdEmpty')
  }

  if (!step.module) {
    return createResult(false, 'validation.workflow.moduleRequired')
  }

  if (!step.params || typeof step.params !== 'object') {
    return createResult(false, 'validation.workflow.paramsRequired')
  }

  return createResult(true)
}
