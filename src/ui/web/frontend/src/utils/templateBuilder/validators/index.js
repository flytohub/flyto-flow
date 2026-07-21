/**
 * UX-HINT ONLY — These validators provide instant feedback while the user types.
 * The backend is the authoritative source of truth for all validation rules.
 * Do NOT rely on these for security or data integrity.
 *
 * Validators Module - Split Exports
 * See GET /api/config/validation-rules.
 *
 * S-Grade: Centralized exports for validation functions.
 *
 * Split structure:
 * - utils.js: Validation utilities (~15 lines)
 * - gridValidators.js: Grid validation (~75 lines)
 * - componentValidators.js: Component validation (~110 lines)
 * - templateValidators.js: Template validation (~115 lines)
 * - fieldValidators.js: Field validation (~90 lines)
 */

// Utilities
export { createResult } from './utils'

// Grid validators
export {
  validateGridSum,
  validateGridValues,
  validateGrid
} from './gridValidators'

// Component validators
export {
  validateComponentRequired,
  validateSelectOptions,
  validateRadioOptions,
  validateSection
} from './componentValidators'

// Template validators
export {
  validateTemplateName,
  validateTemplateId,
  validateTemplateData,
  validateWorkflowStep
} from './templateValidators'

// Field validators
export {
  validateFieldValue,
  validateEmail,
  validateURL,
  validateNumberRange
} from './fieldValidators'
