/**
 * Template Save Module - Split Exports
 *
 * S-Grade: Centralized exports for template save functionality.
 *
 * Split structure:
 * - dataPreparation.js: Save data preparation (~65 lines)
 * - validation.js: Pre-save validation (~45 lines)
 * - saveActions.js: Save operations (~175 lines)
 * - navigationActions.js: Navigation handling (~50 lines)
 * - useTemplateSaveCore.js: Main composable (~90 lines)
 */

// Main composable
export { useTemplateSave } from './useTemplateSaveCore'

// Individual utilities for direct use
export { prepareSaveData } from './dataPreparation'
export { validateBeforeSave } from './validation'
export { createSaveActions } from './saveActions'
export { createNavigationActions } from './navigationActions'
