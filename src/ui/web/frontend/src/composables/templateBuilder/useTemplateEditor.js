/**
 * Template Editor Composable
 *
 * Manages inline template editing dialog state and operations:
 * - Opening/closing the template editor dialog
 * - Loading template data for editing
 * - Saving local templates
 * - Inline template creation from AddNodeMenu
 */

import { ref, reactive } from 'vue'
import { templatesAPI } from '../../api/templates'
import { backendStepsToElementsAsync, elementsToBackendStepsAsync } from '../../utils/converter/asyncConverter'

export function useTemplateEditor({
  elements,
  hasUnsavedChanges,
  createNodeFromModule,
  selectedWorkflowNode,
  showToast,
  t,
  reloadAvailableModules,
  defaultModulesList,
  expertModulesList,
}) {
  const showCreateTemplateModal = ref(false)
  const showTemplateEditor = ref(false)
  const editingTemplate = reactive({
    id: null,
    name: '',
    elements: [],
    ui: { sections: [] },
    loading: false,
    saving: false,
    error: null
  })

  function resetEditingTemplate() {
    editingTemplate.id = null
    editingTemplate.name = ''
    editingTemplate.elements = []
    editingTemplate.ui = { sections: [] }
    editingTemplate.loading = false
    editingTemplate.saving = false
    editingTemplate.error = null
  }

  async function handleEditTemplate({ templateId }) {
    if (!templateId) return

    editingTemplate.id = templateId
    editingTemplate.loading = true
    editingTemplate.error = null
    showTemplateEditor.value = true

    try {
      const result = await templatesAPI.getTemplate(templateId)
      if (!result.ok) {
        editingTemplate.error = result.error || 'Failed to load template'
        return
      }
      const tpl = result.template
      editingTemplate.name = tpl.name || tpl.templateName || 'Template'
      editingTemplate.ui = tpl.ui || { sections: [] }

      const steps = tpl.steps || tpl.workflowSteps || []
      if (steps.length > 0) {
        const converted = await backendStepsToElementsAsync(steps)
        editingTemplate.elements = [...converted.nodes, ...converted.edges]
      } else {
        editingTemplate.elements = []
      }
    } catch (err) {
      console.error('Failed to load template:', err)
      editingTemplate.error = 'Failed to load template'
    } finally {
      editingTemplate.loading = false
    }
  }

  async function updateTemplate(templateId, steps, ui) {
    const result = await templatesAPI.updateTemplate(templateId, { steps, ui })
    if (!result.ok) {
      showToast(t('templateBuilder.messages.saveFailed', 'Failed to save template'), 'error')
      return false
    }
    return true
  }

  async function handleTemplateEditorSave(payload) {
    const { elements: dialogElements, ui, isNested, templateId: nestedTemplateId } = payload

    const tid = isNested ? nestedTemplateId : editingTemplate.id
    if (!tid) return

    editingTemplate.saving = true

    try {
      const steps = await elementsToBackendStepsAsync(dialogElements)

      const success = await updateTemplate(tid, steps, ui)

      if (!success) return

      if (!isNested) showTemplateEditor.value = false

      await reloadAvailableModules()
      showToast(t('templateBuilder.messages.templateSaved', 'Template saved successfully'), 'success')
    } catch (err) {
      console.error('Save error:', err)
      showToast(t('templateBuilder.messages.saveFailed', 'Failed to save template'), 'error')
    } finally {
      editingTemplate.saving = false
    }
  }

  function handleTemplateEditorClose() {
    showTemplateEditor.value = false
    resetEditingTemplate()
  }

  async function handleInlineTemplateCreated(newTemplateId) {
    await reloadAvailableModules()

    const allModules = [...(defaultModulesList.value || []), ...(expertModulesList.value || [])]
    const templateModule = allModules.find(m => {
      const sd = m.sourceData || {}
      return sd.templateId === newTemplateId || sd.libraryId === newTemplateId
    })

    if (templateModule) {
      const newNode = createNodeFromModule(templateModule)
      hasUnsavedChanges.value = true
      selectedWorkflowNode.value = newNode
      showToast(t('templateBuilder.messages.templateCreated', 'Template created — opening editor'), 'success')
      await handleEditTemplate({ templateId: newTemplateId })
    } else {
      showToast(t('templateBuilder.messages.templateModuleNotFound', 'Template created but could not be added to canvas'), 'error')
    }
  }

  return {
    showCreateTemplateModal,
    showTemplateEditor,
    editingTemplate,
    handleEditTemplate,
    handleTemplateEditorSave,
    handleTemplateEditorClose,
    handleInlineTemplateCreated,
  }
}
