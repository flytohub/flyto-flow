/**
 * Template Save Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All save logic split into templateSave/* directory.
 *
 * Split modules:
 * - templateSave/dataPreparation.js: Save data preparation
 * - templateSave/validation.js: Pre-save validation
 * - templateSave/saveActions.js: Save operations
 * - templateSave/navigationActions.js: Navigation handling
 * - templateSave/useTemplateSaveCore.js: Main composable
 */

// Re-export all from split modules
export { useTemplateSave } from './templateSave/index'
