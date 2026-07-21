/**
 * Parameter Renderer - Split Modules Re-exports
 *
 * S-Grade: Centralized exports for param rendering functionality.
 * All modules follow SRP < 200 lines each.
 *
 * Split structure:
 * - paramTypeMaps.js: Type to component mappings (~95 lines)
 * - paramTypeDetection.js: Type detection functions (~140 lines)
 * - paramSchemaParser.js: Schema parsing (~200 lines)
 *
 * Key features:
 * - Simple format support: array → dropdown, boolean/number/string → auto-detect
 * - Object mapping instead of if-else chains
 *
 * NOTE: Form validation and default value computation are handled by the backend.
 * See: services/normalizers/base.py → compute_default_params(), validate on execution.
 */

// Type detection
import { getParamComponentType, getOutputWidgetType, detectFieldConfig } from './paramTypeDetection'

// Schema parsing
import { formatLabel, parseParamsSchema, parseOutputSchema } from './paramSchemaParser'

export {
  getParamComponentType,
  getOutputWidgetType,
  detectFieldConfig,
  formatLabel,
  parseParamsSchema,
  parseOutputSchema
}

export function useParamRenderer() {
  return {
    getParamComponentType,
    getOutputWidgetType,
    detectFieldConfig,
    parseParamsSchema,
    parseOutputSchema,
    formatLabel
  }
}

export default useParamRenderer
