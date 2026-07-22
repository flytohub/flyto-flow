/**
 * Builder Store (Facade)
 *
 * This is a backward-compatible facade that aggregates the split builder stores.
 * New code should import from '@/stores/builder' directly.
 *
 * Split into:
 * - metadataStore: Template name, description, sections, components
 * - uiStateStore: Panel visibility, mode, selection
 * - workflowStore: Nodes, edges, checkpoints
 * - executionStore: Execution, debug, preview state
 */

import { defineStore, storeToRefs } from 'pinia'
import { computed } from 'vue'
import { useBuilderMetadataStore } from './builder/metadataStore'
import { useBuilderUIStore } from './builder/uiStateStore'
import { useBuilderWorkflowStore } from './builder/workflowStore'
import { useBuilderExecutionStore } from './builder/executionStore'

export const useBuilderStore = defineStore('builder', () => {
  // Get individual stores
  const metadataStore = useBuilderMetadataStore()
  const uiStore = useBuilderUIStore()
  const workflowStore = useBuilderWorkflowStore()
  const executionStore = useBuilderExecutionStore()

  // Extract refs from nested stores for proper storeToRefs support
  const {
    activeTab,
    builderMode,
    showTerminal,
    showLayoutPicker,
    showPropertiesPanel,
    showModuleSelector,
    isAddingFirstNode,
    showSaveDialog,
    showTestModal,
    showGridEditDialog,
    nodePropertiesCollapsed,
    showSettingsPanel,
    selectedSection,
    selectedColumn,
    selectedComponentLocation
  } = storeToRefs(uiStore)

  const {
    templateName,
    templateDescription,
    templateId,
    existingTemplateId,
    sections,
    hasUnsavedChanges,
    isSaving,
    isLoading,
    loadError,
    autoSaveEnabled
  } = storeToRefs(metadataStore)

  const {
    nodes,
    edges,
    selectedNodeId,
    viewport,
    checkpoints
  } = storeToRefs(workflowStore)

  const {
    debugMode,
    debugSelectedNodeIds,
    isExecuting,
    executionCurrentStep,
    executionCompletedSteps,
    previewExecutionResult,
    previewExecutionError
  } = storeToRefs(executionStore)

  // ========== Aggregated Getters ==========

  // Computed that combines UI selection with metadata
  const selectedComponent = computed(() => {
    return metadataStore.getComponent(uiStore.selectedComponentLocation)
  })

  // ========== Cross-store Actions ==========

  // These actions coordinate between stores

  function loadTemplate(template) {
    metadataStore.loadTemplate(template)
    // Also load workflow data if present
    if (template.workflow?.nodes) {
      workflowStore.nodes = template.workflow.nodes
    }
    if (template.workflow?.edges) {
      workflowStore.edges = template.workflow.edges
    }
    if (template.workflow?.checkpoints) {
      workflowStore.checkpoints = template.workflow.checkpoints
    }
  }

  function resetTemplate() {
    metadataStore.resetTemplate()
    workflowStore.reset()
  }

  function deleteSection(index) {
    uiStore.clearSectionSelectionOnDelete(index)
    metadataStore.deleteSection(index)
  }

  function moveSection(fromIndex, direction) {
    const toIndex = metadataStore.moveSection(fromIndex, direction)
    if (toIndex !== undefined) {
      uiStore.updateSelectedSectionOnMove(fromIndex, toIndex)
    }
  }

  function deleteComponent(location) {
    uiStore.clearComponentSelectionOnDelete(location)
    metadataStore.deleteComponent(location)
  }

  function selectComponent(sectionIndex, columnIndex, componentIndex) {
    uiStore.selectComponent(sectionIndex, columnIndex, componentIndex)
  }

  function toggleDebugMode() {
    const enabled = executionStore.toggleDebugMode()
    if (enabled) {
      uiStore.setActiveTab('workflow')
    }
    return enabled
  }

  function reset() {
    metadataStore.resetTemplate()
    uiStore.reset()
    workflowStore.reset()
    executionStore.reset()
  }

  // ========== Workflow Actions with Change Tracking ==========

  function setElements(newElements) {
    workflowStore.setElements(newElements)
    metadataStore.hasUnsavedChanges = true
  }

  function addNode(node) {
    workflowStore.addNode(node)
    metadataStore.hasUnsavedChanges = true

  }

  function updateNode(nodeId, data) {
    workflowStore.updateNode(nodeId, data)
    metadataStore.hasUnsavedChanges = true
  }

  function deleteNode(nodeId) {
    workflowStore.deleteNode(nodeId)
    metadataStore.hasUnsavedChanges = true
  }

  function addEdge(edge) {
    workflowStore.addEdge(edge)
    metadataStore.hasUnsavedChanges = true

  }

  function deleteEdge(edgeId) {
    workflowStore.deleteEdge(edgeId)
    metadataStore.hasUnsavedChanges = true
  }

  function toggleCheckpoint(nodeId) {
    workflowStore.toggleCheckpoint(nodeId)
    metadataStore.hasUnsavedChanges = true
  }

  function addCheckpoint(nodeId) {
    workflowStore.addCheckpoint(nodeId)
    metadataStore.hasUnsavedChanges = true
  }

  function removeCheckpoint(nodeId) {
    workflowStore.removeCheckpoint(nodeId)
    metadataStore.hasUnsavedChanges = true
  }

  function clearCheckpoints() {
    workflowStore.clearCheckpoints()
    metadataStore.hasUnsavedChanges = true
  }

  // Return aggregated API for backward compatibility
  return {
    // ===== From metadataStore =====
    // Template Metadata (extracted refs)
    templateName,
    templateId,
    templateDescription,
    existingTemplateId,

    // Template Data (extracted ref)
    sections,

    // Edit State (extracted refs)
    hasUnsavedChanges,
    isSaving,
    isLoading,
    loadError,
    autoSaveEnabled,

    // Template Actions
    setTemplateName: metadataStore.setTemplateName,
    setTemplateDescription: metadataStore.setTemplateDescription,
    loadTemplate,
    resetTemplate,

    // Section Actions
    addSection: metadataStore.addSection,
    updateSectionGrid: metadataStore.updateSectionGrid,
    moveSection,
    deleteSection,

    // Component Actions
    addComponent: metadataStore.addComponent,
    updateComponent: metadataStore.updateComponent,
    deleteComponent,
    duplicateComponent: metadataStore.duplicateComponent,

    // Save Actions
    markSaved: metadataStore.markSaved,
    setSaving: metadataStore.setSaving,
    setAutoSaveEnabled: metadataStore.setAutoSaveEnabled,
    toggleAutoSave: metadataStore.toggleAutoSave,

    // ===== From uiStore =====
    // UI State (extracted refs for storeToRefs compatibility)
    activeTab,
    builderMode,
    showTerminal,
    showLayoutPicker,
    showPropertiesPanel,
    showModuleSelector,
    isAddingFirstNode,
    showSaveDialog,
    showTestModal,
    showGridEditDialog,
    nodePropertiesCollapsed,
    showSettingsPanel,

    // Selection State
    selectedSection,
    selectedColumn,
    selectedComponentLocation,

    // UI Getters (computed - not refs)
    isDev: uiStore.isDev,
    isPreview: uiStore.isPreview,

    // Mode Actions
    setActiveTab: uiStore.setActiveTab,
    setBuilderMode: uiStore.setBuilderMode,

    // Panel Actions
    toggleTerminal: uiStore.toggleTerminal,
    setShowModuleSelector: uiStore.setShowModuleSelector,

    // Selection Actions
    selectSection: uiStore.selectSection,
    selectColumn: uiStore.selectColumn,
    selectComponent,
    clearSelection: uiStore.clearSelection,

    // ===== From workflowStore =====
    // Workflow Elements (extracted refs)
    nodes,
    edges,
    selectedNodeId,

    // Canvas Viewport (extracted ref)
    viewport,
    setViewport: workflowStore.setViewport,

    // Checkpoints (extracted ref)
    checkpoints,
    hasCheckpoints: workflowStore.hasCheckpoints,
    hasCheckpoint: workflowStore.hasCheckpoint,

    // Workflow Getters
    elements: workflowStore.elements,
    selectedNode: workflowStore.selectedNode,

    // Workflow Actions (wrapped to track changes)
    setElements,
    addNode,
    updateNode,
    deleteNode,
    addEdge,
    deleteEdge,
    selectNode: workflowStore.selectNode,

    // Checkpoint Actions (wrapped to track changes)
    toggleCheckpoint,
    addCheckpoint,
    removeCheckpoint,
    clearCheckpoints,

    // ===== From executionStore =====
    // Debug State (extracted refs)
    debugMode,
    debugSelectedNodeIds,

    // Execution State (extracted refs)
    isExecuting,
    executionCurrentStep,
    executionCompletedSteps,

    // Preview State (extracted refs)
    previewExecutionResult,
    previewExecutionError,

    // Debug Actions
    toggleDebugMode,
    setDebugSelectedNodes: executionStore.setDebugSelectedNodes,

    // Execution Actions
    startExecution: executionStore.startExecution,
    setExecutionStep: executionStore.setExecutionStep,
    completeExecutionStep: executionStore.completeExecutionStep,
    stopExecution: executionStore.stopExecution,
    resetExecution: executionStore.resetExecution,

    // Preview Actions
    setPreviewResult: executionStore.setPreviewResult,
    setPreviewError: executionStore.setPreviewError,
    clearPreviewState: executionStore.clearPreviewState,

    // ===== Aggregated =====
    selectedComponent,

    // Reset all
    reset
  }
})
