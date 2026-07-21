/**
 * Builder Metadata Store Core
 *
 * S-Grade: Main metadata store.
 * Single responsibility: Compose metadata functionality.
 */

import { defineStore } from 'pinia'
import { createMetadataState, createMetadataGetters } from './state'
import { createTemplateActions } from './templateActions'
import { createSectionActions, createComponentActions, createSaveActions } from './sectionActions'

export const useBuilderMetadataStore = defineStore('builder-metadata', () => {
  // Create state
  const state = createMetadataState()

  // Create getters
  const getters = createMetadataGetters(state)

  // Create actions
  const templateActions = createTemplateActions(state)
  const sectionActions = createSectionActions(state)
  const componentActions = createComponentActions(state)
  const saveActions = createSaveActions(state)

  return {
    // State (exclude counters from external access)
    templateName: state.templateName,
    templateId: state.templateId,
    templateDescription: state.templateDescription,
    existingTemplateId: state.existingTemplateId,
    templateCreatorId: state.templateCreatorId,
    templateMutability: state.templateMutability,
    templateVisibility: state.templateVisibility,
    templateListed: state.templateListed,
    isWorkflowVisible: state.isWorkflowVisible,
    sections: state.sections,
    hasUnsavedChanges: state.hasUnsavedChanges,
    isSaving: state.isSaving,
    isLoading: state.isLoading,
    loadError: state.loadError,
    autoSaveEnabled: state.autoSaveEnabled,

    // Getters
    ...getters,

    // Actions
    ...templateActions,
    ...sectionActions,
    ...componentActions,
    ...saveActions,
  }
})
