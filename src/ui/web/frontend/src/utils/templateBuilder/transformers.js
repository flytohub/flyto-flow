/**
 * Data Transformation Tool
 *
 * S-Grade: Re-export layer for backward compatibility.
 * All transformers split into transformers/* directory.
 *
 * Split modules:
 * - transformers/objectUtils.js: Deep clone, merge, clean
 * - transformers/sectionTransformers.js: Section flattening
 * - transformers/optionTransformers.js: Option parsing
 * - transformers/idUtils.js: ID normalization, slug
 * - transformers/exportTransformers.js: Import/export
 *
 * NOTE: Workflow conversion is handled by utils/converter (asyncConverter)
 */

// Re-export all from split modules
export {
  // Object utilities
  deepClone,
  removeEmptyValues,
  mergeProps,

  // Section transformers
  flattenSectionsToComponents,
  componentsToSections,

  // Option transformers
  parseOptionsText,
  stringifyOptions,

  // ID utilities
  normalizeComponentId,
  generateSlug,

  // Export transformers
  transformToExportFormat,
  transformFromImportFormat,
  updateComponentProps,
  extractTemplateSummary
} from './transformers/index'
