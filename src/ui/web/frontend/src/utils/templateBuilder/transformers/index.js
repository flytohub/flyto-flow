/**
 * Transformers Module - Split Exports
 *
 * S-Grade: Centralized exports for data transformation functions.
 *
 * Split structure:
 * - objectUtils.js: Deep clone, merge, clean (~80 lines)
 * - sectionTransformers.js: Section flattening (~60 lines)
 * - optionTransformers.js: Option parsing (~65 lines)
 * - idUtils.js: ID normalization, slug (~40 lines)
 * - exportTransformers.js: Import/export (~70 lines)
 *
 * NOTE: Workflow conversion is handled by utils/converter (asyncConverter)
 */

// Object utilities
export {
  deepClone,
  removeEmptyValues,
  mergeProps
} from './objectUtils'

// Section transformers
export {
  flattenSectionsToComponents,
  componentsToSections
} from './sectionTransformers'

// Option transformers
export {
  parseOptionsText,
  stringifyOptions
} from './optionTransformers'

// ID utilities
export {
  normalizeComponentId,
  generateSlug
} from './idUtils'

// Export transformers
export {
  transformToExportFormat,
  transformFromImportFormat,
  updateComponentProps,
  extractTemplateSummary
} from './exportTransformers'
