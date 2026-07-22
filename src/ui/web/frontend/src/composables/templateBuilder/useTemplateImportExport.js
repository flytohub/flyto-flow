/**
 * Template Import/Export Composable
 * Handles importing and exporting template data
 */

import { ref, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import yaml from 'js-yaml'
import { importFromFile } from '../../services/templateDataService'
import { elementsToBackendStepsAsync, ConversionError } from '../../utils/converter'
import { downloadText } from '@/services/domUtils'

/** Flatten params fields to component level for builder compatibility */
const _FLATTEN_FIELDS = ['inputType', 'placeholder', 'default', 'required']
function _normalizeSections(sections) {
  for (const sec of sections) {
    for (const col of (sec.columnsData || [])) {
      for (const comp of (col.components || [])) {
        if (comp.params) {
          for (const field of _FLATTEN_FIELDS) {
            if (field in comp.params && comp.params[field] != null && comp.params[field] !== '') {
              if (!(field in comp) || comp[field] == null || comp[field] === '') {
                comp[field] = comp.params[field]
              }
            }
          }
        }
      }
    }
  }
}

/**
 * Create import/export composable
 * @param {Object} options
 * @param {Ref} options.elements - Workflow elements
 * @param {Ref} options.templateId - Template ID
 * @param {Ref} options.templateName - Template name
 * @param {Ref} options.templateDescription - Template description
 * @param {Ref} options.sections - UI sections
 * @param {Ref} options.activeTab - Active tab
 * @param {Ref} options.modulesMetadata - Modules metadata
 * @param {Ref} options.checkpoints - Human Checkpoint node IDs
 * @param {Function} options.showToast - Toast notification function
 * @param {Function} options.onAutoLayout - Callback to trigger auto layout after import
 */
export function useTemplateImportExport(options) {
  const {
    elements,
    templateId,
    templateName,
    templateDescription,
    sections,
    activeTab,
    modulesMetadata,
    checkpoints,
    showToast,
    onAutoLayout
  } = options

  const { t } = useI18n()

  // File input ref
  const importFileInput = ref(null)

  // Import guard to prevent concurrent imports
  const isImporting = ref(false)

  /**
   * Trigger file import dialog
   */
  function triggerImport() {
    importFileInput.value?.click()
  }

  /**
   * Handle file import
   * @param {Event} event - File input change event
   */
  async function handleImportFile(event) {
    const file = event.target.files?.[0]
    if (!file) return

    // Prevent concurrent imports
    if (isImporting.value) {
      showToast(t('templateBuilder.messages.importInProgress') || 'Import already in progress', 'warning')
      event.target.value = ''
      return
    }

    isImporting.value = true
    try {
      const getModuleById = (moduleId) => modulesMetadata.value[moduleId]
      const result = await importFromFile(file, { getModuleById, strictMode: false })

      if (!result.success) {
        showToast(t('templateBuilder.messages.importFailed', { error: result.errors.join(', ') }), 'error')
        return
      }

      if (result.format === 'json' && result.data) {
        // Extract and apply imported data to store
        if (result.data.templateId || result.data.template_id) templateId.value = result.data.templateId || result.data.template_id
        if (result.data.templateName || result.data.template_name || result.data.name) {
          templateName.value = result.data.templateName || result.data.template_name || result.data.name
        }
        if (result.data.description || result.data.templateDescription || result.data.template_description) {
          templateDescription.value = result.data.description || result.data.templateDescription || result.data.template_description
        }
        if (result.data.ui?.sections) {
          sections.value = result.data.ui.sections
        }


        showToast(t('templateBuilder.messages.jsonImportSuccess'), 'success')
      } else if (result.format === 'yaml') {
        if (result.workflowMeta?.id) templateId.value = result.workflowMeta.id
        if (result.workflowMeta?.name) templateName.value = result.workflowMeta.name
        if (result.workflowMeta?.description) {
          templateDescription.value = result.workflowMeta.description
        }

        if (result.warnings.length > 0) {
          showToast(t('templateBuilder.messages.yamlImportWarnings', { count: result.warnings.length }), 'warning')
        }

        // Single atomic assignment — avoids isSyncing race condition in WorkflowCanvas
        elements.value = [...result.nodes, ...result.edges]

        // Import checkpoints if present
        if (result.checkpoints && checkpoints) {
          checkpoints.value = result.checkpoints
        }

        // Restore UI builder sections from _ui block
        if (result._ui?.builder?.sections && sections) {
          _normalizeSections(result._ui.builder.sections)
          sections.value = result._ui.builder.sections
        }

        // Auto layout after import (skip if _ui has positions — they're already in nodes)
        await nextTick()
        if (onAutoLayout && !result._ui?.positions) {
          onAutoLayout()
        }


        showToast(t('templateBuilder.messages.yamlImportSuccess', { count: result.nodes.length }), 'success')
      }
    } catch (error) {
      showToast(t('templateBuilder.messages.importFailed', { error: error.message }), 'error')
    } finally {
      isImporting.value = false
      event.target.value = ''
    }
  }

  /**
   * Handle export based on active tab
   */
  async function handleExport() {
    if (activeTab.value === 'workflow') {
      await exportYAML()
    }
  }

  /**
   * Export workflow as YAML (unified format: execution + _ui)
   *
   * The _ui block contains positions and builder sections.
   * flyto-core ignores _ui; Flyto2 Flow restores it on import.
   */
  async function exportYAML() {
    const allElements = elements.value
    const nodes = allElements.filter(el => el.id && !el.source && !el.target)
    const edges = allElements.filter(el => el.source && el.target)

    if (nodes.length === 0) {
      showToast(t('templateBuilder.messages.noSteps', 'No workflow steps to export'), 'warning')
      return
    }

    try {
      // Backend is single source of truth for conversion
      const steps = await elementsToBackendStepsAsync(allElements)

      // Build workflow object
      const workflow = {
        id: templateId.value || 'workflow',
        name: templateName.value || 'Untitled Workflow',
        version: '1.0.0',
        steps
      }

      // Preserve edges for round-trip fidelity
      if (edges.length > 0) {
        workflow.edges = edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle,
          targetHandle: edge.targetHandle,
          type: edge.type,
          data: edge.data,
          label: edge.label
        }))
      }

      // Checkpoints
      if (checkpoints?.value?.length > 0) {
        workflow.checkpoints = checkpoints.value
      }

      // Build _ui block — separate UI metadata from execution data
      const _ui = {}

      // Extract positions from steps into _ui.positions (matches backend template_yaml.py format)
      const positions = {}
      for (const step of (workflow.steps || [])) {
        if (step.position_x != null || step.position_y != null) {
          positions[step.id] = [step.position_x || 0, step.position_y || 0]
          delete step.position_x
          delete step.position_y
        }
      }
      if (Object.keys(positions).length) _ui.positions = positions

      // Include builder sections (UI Design Tab form components)
      if (sections?.value?.length) {
        _ui.builder = { sections: sections.value }
      }

      if (Object.keys(_ui).length) {
        workflow._ui = _ui
      }

      const yamlContent = yaml.dump(workflow, { indent: 2, lineWidth: -1 })
      downloadText(yamlContent, `${templateId.value || 'workflow'}.yaml`, 'text/yaml')


      showToast(t('templateBuilder.messages.yamlExportSuccess'), 'success')
    } catch (err) {
      const msg = err instanceof ConversionError
        ? t('templateBuilder.messages.conversionError', 'Failed to convert workflow. Please try again.')
        : (err.message || 'Export failed')
      showToast(msg, 'error')
    }
  }

  return {
    importFileInput,
    isImporting,
    triggerImport,
    handleImportFile,
    handleExport,
    exportYAML
  }
}
