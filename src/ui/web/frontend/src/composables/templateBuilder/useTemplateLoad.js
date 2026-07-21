/**
 * Template Load Composable
 *
 * Handles loading existing templates from API or local storage.
 *
 * Note: Uses async conversion to ensure backend is single source of truth.
 * ConversionError is handled with user-friendly messages.
 */

import { nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { templatesAPI } from '../../api/templates'
import {
  backendStepsToElementsAsync,
  debugLogSteps,
  ConversionError,
  ConversionErrorCodes
} from '../../utils/converter'

export function useTemplateLoad({
  // State refs
  isLoadingTemplate,
  loadError,
  existingTemplateId,
  templateName,
  templateId,
  templateDescription,
  templateCreatorId,
  templateMutability,
  templateVisibility,
  templateListed,
  isWorkflowVisible,  // Backend determines if workflow should be visible
  sections,
  elements,
  viewport,
  activeTab,
  hasUnsavedChanges,
  // Error handling
  errorHandling,
  // Metadata
  modulesMetadata,
  iconMap,
  // Notifications
  showToast
}) {
  const { t } = useI18n()

  /**
   * Load an existing template by ID
   */
  async function loadExistingTemplate(id) {
    isLoadingTemplate.value = true
    loadError.value = null

    try {
      let template

      const response = await templatesAPI.getTemplate(id)

      // API returns { ok: true, template: {...} } or { ok: false, error: '...' }
      if (!response.ok || !response.template) {
        const errorMsg = response.error || t('templateBuilder.messages.templateNotFound')
        loadError.value = errorMsg
        showToast(errorMsg, 'error')
        return
      }

      template = response.template

      // Set template metadata
      existingTemplateId.value = template.id
      const name = template.templateName || template.template_name || template.name || t('templateBuilder.toolbar.templateNamePlaceholder')
      templateName.value = name
      templateId.value = template.templateId || template.template_id || template.id
      templateCreatorId.value = template.creatorId || template.creator_id || null
      templateMutability.value = template.mutability || 'fork_on_use'
      templateVisibility.value = template.visibility || 'private'
      templateListed.value = template.listed !== false

      // SECURITY: Store workflow visibility from backend
      // Backend determines visibility based on mutability and ownership
      const workflowVisible = template.is_workflow_visible !== false
      if (isWorkflowVisible) {
        isWorkflowVisible.value = workflowVisible
      }

      if (!workflowVisible) {
        showToast(t('templateBuilder.messages.workflowLocked', 'This workflow is protected. You can use this template but cannot view the internal logic.'), 'warning')
        // Clear workflow elements - backend already returned empty steps
        elements.value = []
      }

      // Load UI sections
      if (template.ui?.sections && template.ui.sections.length > 0) {
        // Normalize: flatten params fields to component level for builder compatibility
        // YAML community templates may nest inputType/placeholder under params
        for (const sec of template.ui.sections) {
          for (const col of (sec.columnsData || [])) {
            for (const comp of (col.components || [])) {
              if (comp.params) {
                for (const field of ['inputType', 'placeholder', 'default', 'required']) {
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
        sections.value = template.ui.sections
      } else if (template.ui?.components && template.ui.components.length > 0) {
        // Migration: convert old ui.components format to ui.sections
        // Put all components in a single section with a single column
        sections.value = [{
          id: 'section_migrated_1',
          title: 'Form',
          columns: 1,
          columnsData: [{
            id: 'col_migrated_1',
            width: '100%',
            components: template.ui.components.map(comp => ({
              ...comp,
              // Ensure component has required fields
              id: comp.id || `comp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
              type: comp.type || 'input',
              label: comp.label || comp.params?.label || 'Input',
              params: comp.params || {}
            }))
          }]
        }]
      }

      // Load workflow: always use backend as single source of truth
      if (template.steps && template.steps.length > 0) {
        debugLogSteps('Loading from backend', template.steps)
        const getModuleById = (moduleId) => modulesMetadata.value[moduleId]
        const result = await backendStepsToElementsAsync(template.steps, { getModuleById, iconMap })

        elements.value = [...result.nodes, ...result.edges]
        debugLogSteps('Converted to elements', result.nodes)
        activeTab.value = 'workflow'
      }

      // Load description
      if (template.templateDescription || template.template_description || template.description) {
        templateDescription.value = template.templateDescription || template.template_description || template.description
      }

      // Load saved viewport (zoom/pan state)
      if (template.viewport && viewport) {
        viewport.value = template.viewport
      }

      // Restore error handling configuration
      if (errorHandling && template.error_workflow_id) {
        errorHandling.value = {
          onFailure: 'run_workflow',
          errorWorkflowId: template.error_workflow_id,
          passErrorContext: template.error_handling?.passErrorContext ?? true
        }
      }

      // Wait for all reactive updates to complete
      await nextTick()
      await nextTick()
      // FE-P0-003: Only clear hasUnsavedChanges on successful load
      hasUnsavedChanges.value = false
    } catch (error) {
      // Handle ConversionError with specific user-friendly messages
      let errorMsg
      if (error instanceof ConversionError) {
        errorMsg = error.code === ConversionErrorCodes.BACKEND_UNAVAILABLE
          ? t('templateBuilder.messages.connectionError', 'Unable to connect to server. Please check your connection.')
          : t('templateBuilder.messages.conversionError', 'Failed to load workflow format. Please try again.')
      } else {
        errorMsg = error.message || t('templateBuilder.messages.loadTemplateFailed')
      }
      loadError.value = errorMsg
      showToast(errorMsg, 'error')
    } finally {
      // Only reset the loading flag, not hasUnsavedChanges (which is handled above on success)
      isLoadingTemplate.value = false
    }
  }

  return {
    loadExistingTemplate
  }
}
