/**
 * Builder Metadata State
 *
 * S-Grade: State refs and getters.
 * Single responsibility: Metadata state management.
 */

import { ref, computed } from 'vue'

/**
 * Create metadata store state
 * @returns {Object} State refs and counters
 */
export function createMetadataState() {
  // Template Metadata
  const templateName = ref('')
  const templateId = ref('new_template')
  const templateDescription = ref('')
  const existingTemplateId = ref(null)
  const templateCreatorId = ref(null)
  const templateMutability = ref('fork_on_use')
  const templateVisibility = ref('private')
  const templateListed = ref(false)
  const isWorkflowVisible = ref(true)  // Backend determines if workflow is visible

  // Template UI Sections
  const sections = ref([])

  // Edit State
  const hasUnsavedChanges = ref(false)
  const isSaving = ref(false)
  const isLoading = ref(false)
  const loadError = ref(null)
  const autoSaveEnabled = ref(true)

  // Counters (mutable)
  const counters = {
    section: 1,
    component: 1
  }

  return {
    templateName,
    templateId,
    templateDescription,
    existingTemplateId,
    templateCreatorId,
    templateMutability,
    templateVisibility,
    templateListed,
    isWorkflowVisible,
    sections,
    hasUnsavedChanges,
    isSaving,
    isLoading,
    loadError,
    autoSaveEnabled,
    counters,
  }
}

/**
 * Create metadata store getters
 * @param {Object} state - State refs
 * @returns {Object} Computed getters
 */
export function createMetadataGetters(state) {
  const { existingTemplateId, templateMutability } = state

  const isReadOnly = computed(() => {
    if (!existingTemplateId.value) return false
    return templateMutability.value === 'locked'
  })

  return {
    isReadOnly,
  }
}
