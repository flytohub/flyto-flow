/**
 * Step Converter Index
 *
 * Backend is single source of truth for workflow format conversion.
 * Frontend only handles position mapping and visual styling.
 *
 * Backend API endpoints:
 * - POST /api/workflows/vueflow-to-steps
 * - POST /api/workflows/steps-to-vueflow
 */

// Async converters (backend API)
export {
  elementsToBackendStepsAsync,
  backendStepsToElementsAsync,
  ConversionError,
  ConversionErrorCodes
} from './asyncConverter'

// Module type checkers - 5-Star: functions only, no deprecated constants
export {
  isLoopModule,
  isBranchModule,
  isSwitchModule,
  isContainerModule
} from './constants'

// Helper utilities
export {
  extractRequiredPermissions,
  extractRawModuleId,
  debugLogSteps
} from './helpers'
