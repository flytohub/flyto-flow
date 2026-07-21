/**
 * Validation Utilities
 *
 * S-Grade: Common validation helpers.
 * Single responsibility: Provide validation result factory.
 */

/**
 * Create validation result
 * @param {boolean} valid
 * @param {string} errorKey - i18n key
 * @param {object} params - interpolation params for i18n
 */
export function createResult(valid, errorKey = null, params = {}) {
  return { valid, errorKey, params }
}
