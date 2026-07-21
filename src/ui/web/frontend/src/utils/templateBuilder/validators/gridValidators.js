/**
 * UX-HINT ONLY — These validators provide instant feedback while the user types.
 * The backend is the authoritative source of truth for all validation rules.
 * Do NOT rely on these for security or data integrity.
 *
 * Grid Validators
 * See GET /api/config/validation-rules.
 *
 * S-Grade: Grid layout validation.
 * Single responsibility: Validate grid configurations.
 */

import { createResult } from './utils'

/**
 * Validate grid sum equals 12
 * @param {Array<number>} gridArray - Grid array
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object, sum?: number }
 */
export function validateGridSum(gridArray) {
  if (!Array.isArray(gridArray)) {
    return createResult(false, 'validation.grid.mustBeArray')
  }

  if (gridArray.length === 0) {
    return createResult(false, 'validation.grid.cannotBeEmpty')
  }

  const sum = gridArray.reduce((acc, val) => {
    const num = parseInt(val)
    return acc + (isNaN(num) ? 0 : num)
  }, 0)

  if (sum !== 12) {
    return { valid: false, errorKey: 'validation.grid.sumMustBe12', params: { sum }, sum }
  }

  return { valid: true, sum }
}

/**
 * Validate each value in grid array
 * @param {Array<number>} gridArray - Grid array
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateGridValues(gridArray) {
  if (!Array.isArray(gridArray)) {
    return createResult(false, 'validation.grid.mustBeArray')
  }

  for (let i = 0; i < gridArray.length; i++) {
    const val = parseInt(gridArray[i])

    if (isNaN(val)) {
      return createResult(false, 'validation.grid.valueMustBeNumber', { index: i })
    }

    if (val < 1) {
      return createResult(false, 'validation.grid.valueTooSmall', { index: i, min: 1 })
    }

    if (val > 12) {
      return createResult(false, 'validation.grid.valueTooLarge', { index: i, max: 12 })
    }
  }

  return createResult(true)
}

/**
 * Validate complete grid configuration
 * @param {Array<number>} gridArray - Grid array
 * @returns {Object} { valid: boolean, errorKey?: string, params?: object }
 */
export function validateGrid(gridArray) {
  // Validate values first
  const valuesResult = validateGridValues(gridArray)
  if (!valuesResult.valid) {
    return valuesResult
  }

  // Then validate sum
  return validateGridSum(gridArray)
}
