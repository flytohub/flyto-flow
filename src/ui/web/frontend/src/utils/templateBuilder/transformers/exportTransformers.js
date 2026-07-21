/**
 * Export Transformers
 *
 * S-Grade: Import/export format conversions.
 * Single responsibility: Handle template import/export transformations.
 */

import { deepClone } from './objectUtils'
import { flattenSectionsToComponents } from './sectionTransformers'

/**
 * Transform template data to export format (with metadata)
 * @param {Object} templateData - Template data
 * @returns {Object} Data in export format
 */
export function transformToExportFormat(templateData) {
  return {
    version: '1.0',
    exported_at: new Date().toISOString(),
    template: deepClone(templateData)
  }
}

/**
 * Restore template from import data
 * @param {Object} importData - Imported data
 * @returns {Object} Template data
 */
export function transformFromImportFormat(importData) {
  // Support two formats:
  // 1. New format { version, exported_at, template }
  // 2. Old format (direct template data)

  if (importData.template) {
    // New format
    return deepClone(importData.template)
  } else {
    // Old format
    return deepClone(importData)
  }
}

/**
 * Update component properties (merge, not replace)
 * @param {Object} component - Component object
 * @param {Object} updates - Properties to update
 * @returns {Object} Updated component
 */
export function updateComponentProps(component, updates) {
  return {
    ...component,
    ...updates
  }
}

/**
 * Extract template summary information
 * @param {Object} templateData - Template data
 * @returns {Object} Summary information
 */
export function extractTemplateSummary(templateData) {
  const sections = templateData.ui?.sections || []
  const totalComponents = flattenSectionsToComponents(sections).length

  return {
    id: templateData.template_id,
    name: templateData.name,
    description: templateData.description || '',
    version: templateData.version || '1.0',
    sectionsCount: sections.length,
    componentsCount: totalComponents,
    hasWorkflow: Array.isArray(templateData.steps) && templateData.steps.length > 0
  }
}
