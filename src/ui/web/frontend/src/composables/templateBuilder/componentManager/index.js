/**
 * Component Manager Module
 *
 * S-Grade: Re-export all component manager functionality.
 *
 * Split modules:
 * - defaultConfig.js: Default component configurations
 * - crudActions.js: CRUD operations
 * - useComponentManagerCore.js: Main composable
 */

// Main composable
export { useComponentManager } from './useComponentManagerCore'

// Config utilities
export {
  applyDefaultConfig,
  FORM_TYPES,
  isFormType
} from './defaultConfig'

// Actions factory (for testing/composition)
export { createCrudActions } from './crudActions'
