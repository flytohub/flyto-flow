/**
 * Validation Tool
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All validators split into validators/* directory.
 *
 * Split modules:
 * - validators/utils.js: Validation utilities
 * - validators/gridValidators.js: Grid validation
 * - validators/componentValidators.js: Component validation
 * - validators/templateValidators.js: Template validation
 * - validators/fieldValidators.js: Field validation
 *
 * Returns errorKey for i18n translation instead of hardcoded messages
 * Caller should use: t(result.errorKey, result.params) to get translated message
 */

// Re-export all from split modules
export {
  // Utilities
  createResult,

  // Grid validators
  validateGridSum,
  validateGridValues,
  validateGrid,

  // Component validators
  validateComponentRequired,
  validateSelectOptions,
  validateRadioOptions,
  validateSection,

  // Template validators
  validateTemplateName,
  validateTemplateId,
  validateTemplateData,
  validateWorkflowStep,

  // Field validators
  validateFieldValue,
  validateEmail,
  validateURL,
  validateNumberRange
} from './validators/index'
