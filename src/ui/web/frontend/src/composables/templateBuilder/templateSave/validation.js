/**
 * Save Validation
 *
 * S-Grade: Validate template before saving.
 * Single responsibility: Pre-save validation.
 */

import { validateWorkflow } from '../../workflowEditor/useWorkflowValidation'
import { DEFAULTS } from '@/config/defaults'

/**
 * Validate workflow before save
 * Calls backend core API for validation.
 * @param {Object} options
 * @param {Ref} options.elements - Workflow elements
 * @param {Ref} options.templateData - Template data
 * @param {Function} options.showToast - Toast notification function
 * @param {Function} options.t - i18n translation function
 * @returns {Promise<boolean>} True if valid
 */
function getNodeIdFromPath(path) {
  if (!path) return null
  const match = String(path).match(/nodes\[(.+?)\]/)
  return match ? match[1] : null
}

/**
 * Apply validation results to elements without corrupting them
 * FE-P1-011: Ensures validation data is safely added without corrupting element structure
 */
function applyValidationToElements(elements, validation) {
  if (!Array.isArray(elements)) return elements

  // Safely extract issues with default empty arrays
  const errors = Array.isArray(validation?.errors) ? validation.errors : []
  const warnings = Array.isArray(validation?.warnings) ? validation.warnings : []

  const issues = [
    ...errors.map(issue => ({ ...issue, severity: 'error' })),
    ...warnings.map(issue => ({ ...issue, severity: 'warning' }))
  ]
  const nodeMap = new Map()

  for (const issue of issues) {
    const nodeId = issue?.meta?.node_id || getNodeIdFromPath(issue?.path)
    if (!nodeId) continue
    const entry = nodeMap.get(nodeId) || { errors: 0, warnings: 0, issues: [] }
    if (issue.severity === 'error') entry.errors += 1
    if (issue.severity === 'warning') entry.warnings += 1
    entry.issues.push(issue)
    nodeMap.set(nodeId, entry)
  }

  // Create new array with validation data - never mutate original
  return elements.map(el => {
    // Skip edges and invalid elements
    if (!el?.id || el.source || el.target) return el
    // Skip elements without data
    if (!el.data) return el

    const validationData = nodeMap.get(el.id) || null

    // Return new element with validation data added
    // This preserves all original properties and only adds validation
    return {
      ...el,
      data: {
        ...el.data,
        validation: validationData
      }
    }
  })
}

/**
 * Validate workflow before save
 * @param {Object} options
 * @param {Ref} options.elements - Workflow elements
 * @param {Ref} options.templateData - Template data
 * @param {Function} options.showToast - Toast notification function
 * @param {Function} options.t - i18n translation function
 * @param {boolean} [options.applyValidation=true] - Whether to apply validation state to elements
 * @returns {Promise<{valid: boolean, validatedElements?: Array}>}
 */
export async function validateBeforeSave(options) {
  const { elements, templateData, showToast, t, applyValidation = true } = options

  // Validate template name
  if (!templateData.value.name || !templateData.value.name.trim()) {
    showToast(t('templateBuilder.alerts.enterTemplateName'), 'warning')
    return { valid: false }
  }

  // Validate workflow via backend API
  const validation = await validateWorkflow(elements.value)

  // Compute validated elements (without modifying the original)
  let validatedElements = elements.value

  // Show errors if any
  if (!validation.ok) {
    validatedElements = applyValidationToElements(elements.value, validation)
    if (applyValidation) {
      elements.value = validatedElements
    }
    const errorMessages = validation.errors.map(e => e.message || JSON.stringify(e)).join('\n')
    showToast(t('templateBuilder.alerts.workflowValidationError', { errors: errorMessages }), 'error', DEFAULTS.TIMING.TOAST_DURATION_ERROR)
    return { valid: false, validatedElements }
  }

  // Show warnings (non-blocking)
  if (validation.warnings.length > 0) {
    validatedElements = applyValidationToElements(elements.value, validation)
    if (applyValidation) {
      elements.value = validatedElements
    }
    showToast(t('templateBuilder.alerts.workflowValidationWarnings', { count: validation.warnings.length }), 'warning')
  } else {
    validatedElements = applyValidationToElements(elements.value, { errors: [], warnings: [] })
    if (applyValidation) {
      elements.value = validatedElements
    }
  }

  return { valid: true, validatedElements }
}
