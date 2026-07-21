/**
 * UX-HINT ONLY — These validators provide instant feedback while the user types.
 * The backend is the authoritative source of truth for all validation rules.
 * Do NOT rely on these for security or data integrity.
 *
 * Component Validators
 * See GET /api/config/validation-rules.
 *
 * S-Grade: UI component validation.
 * Single responsibility: Validate component configurations.
 */

import { createResult } from './utils'
import { validateGrid } from './gridValidators'

/**
 * Validate component required fields
 * @param {Object} component - Component object
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateComponentRequired(component) {
  if (!component) {
    return createResult(false, 'validation.component.empty')
  }

  if (!component.type) {
    return createResult(false, 'validation.component.typeEmpty')
  }

  if (!component.id) {
    return createResult(false, 'validation.component.idEmpty')
  }

  if (!component.label || component.label.trim() === '') {
    return createResult(false, 'validation.component.labelEmpty')
  }

  return createResult(true)
}

/**
 * Validate Select component options
 * @param {Array<Object>} options - Option array
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateSelectOptions(options) {
  if (!Array.isArray(options)) {
    return createResult(false, 'validation.options.mustBeArray')
  }

  if (options.length === 0) {
    return createResult(false, 'validation.options.atLeastOne')
  }

  for (let i = 0; i < options.length; i++) {
    const option = options[i]

    if (!option.label || option.label.trim() === '') {
      return createResult(false, 'validation.options.labelEmpty', { index: i })
    }

    if (!option.value) {
      return createResult(false, 'validation.options.valueEmpty', { index: i })
    }
  }

  return createResult(true)
}

/**
 * Validate Radio component options
 * @param {Array<Object>} options - Option array
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateRadioOptions(options) {
  // Radio option validation rules are the same as Select
  return validateSelectOptions(options)
}

/**
 * Validate section structure
 * @param {Object} section - Section object
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateSection(section) {
  if (!section) {
    return createResult(false, 'validation.section.empty')
  }

  if (!section.id) {
    return createResult(false, 'validation.section.idEmpty')
  }

  if (!section.columns || section.columns < 1) {
    return createResult(false, 'validation.section.columnsMin', { min: 1 })
  }

  if (!Array.isArray(section.grid)) {
    return createResult(false, 'validation.section.gridMustBeArray')
  }

  if (!Array.isArray(section.columnsData)) {
    return createResult(false, 'validation.section.columnsDataMustBeArray')
  }

  if (section.columnsData.length !== section.columns) {
    return createResult(false, 'validation.section.columnsMismatch', {
      actual: section.columnsData.length,
      expected: section.columns
    })
  }

  // Validate grid
  const gridResult = validateGrid(section.grid)
  if (!gridResult.valid) {
    return gridResult
  }

  return createResult(true)
}
