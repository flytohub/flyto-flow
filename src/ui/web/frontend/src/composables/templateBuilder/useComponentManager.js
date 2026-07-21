/**
 * Component Manager Composable
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All component manager logic split into componentManager/* directory.
 *
 * Split modules:
 * - componentManager/defaultConfig.js: Default component configurations
 * - componentManager/crudActions.js: CRUD operations
 * - componentManager/useComponentManagerCore.js: Main composable
 */

// Re-export all from split modules
export {
  useComponentManager,
  applyDefaultConfig,
  FORM_TYPES,
  isFormType,
  createCrudActions
} from './componentManager/index'
