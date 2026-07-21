/**
 * Workflow Converter - Re-exports
 *
 * All conversion logic is on the backend (single source of truth).
 * This module re-exports shared helpers used by other frontend code.
 */

// Re-export shared helpers from utils/converter (single source of truth)
export {
  resolveSwitchCaseKey,
  resolveSwitchCaseHandleId,
  parseParams,
  extractRawModuleId
} from '@/utils/converter/helpers'
