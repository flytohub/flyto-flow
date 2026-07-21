<template>
  <div class="template-builder-page">
    <!-- Loading Skeleton -->
    <BuilderSkeleton v-if="!isPageReady" />

    <!-- Main Content (hidden until ready) -->
    <template v-if="isPageReady">

    <!-- Header -->
    <BuilderHeader
      :template-name="templateName"
      :active-tab="activeTab"
      :is-executing="isExecuting"
      :existing-template-id="existingTemplateId"
      :auto-save-enabled="autoSaveEnabled"
      :show-debug-toolbar="showDebugToolbar"
      :active-debug-panel="activeDebugPanel"
      :can-replay="!isExecuting && currentExecutionId !== null"
      :has-timeline="timelineNodes.length > 0"
      :test-status="testStatus"
      :locked-version-count="lockedVersionCount"
      :execution-count="executionCount"
      @back="handleBack"
      @run="runWorkflow"
      @stop="stopExecution"
      @save="saveTemplate"
      @save-as-new="saveAsNewTemplate"
      @toggle-auto-save="handleToggleAutoSave"
      @toggle-settings="handleToggleSettings"
      @tidy-nodes="handleTidyNodes"
      @toggle-debug-panel="handleToggleDebugPanel"
      @show-upgrade="showUpgradeModal = true"
      @toggle-collaboration="showCollaborationPanel = !showCollaborationPanel"
      :has-browser="hasBrowser"
      :is-recording="recordingStore.isRecording"
      @toggle-browser="showBrowserPanel = !showBrowserPanel"
      @start-recording="handleStartRecording"
      @stop-recording="handleStopRecording"
    />

    <!-- Recording Panel (floating) -->
    <RecordingPanel
      @stop="handleStopRecording"
      @apply="handleApplyRecording"
      @discard="recordingStore.reset()"
    />

    <!-- All Dialogs & Modals -->
    <BuilderDialogs
      :active-tab="activeTab"
      :show-save-dialog="showSaveDialog"
      :show-terminal="showTerminal"
      :show-test-modal="showTestModal"
      :test-result="testResult"
      :show-grid-edit-dialog="showGridEditDialog"
      :temp-grid-values="tempGridValues"
      :confirm-dialog="confirmDialog"
      :show-create-template-modal="showCreateTemplateModal"
      :show-template-editor="showTemplateEditor"
      :editing-template="editingTemplate"
      :default-modules="defaultModulesList"
      :expert-modules="expertModulesList"
      :modules-metadata="modulesMetadata"
      :backend-steps-to-elements="backendStepsToElementsAsync"
      :toast="toast"
      :show-module-selector="showModuleSelector"
      :module-categories="moduleCategories"
      :available-steps="availableSteps"
      :is-loading-modules="isLoadingModules"
      :is-adding-first-node="builderStore.isAddingFirstNode"
      :show-upgrade-modal="showUpgradeModal"
      @update:show-save-dialog="showSaveDialog = $event"
      @leave-without-saving="leaveWithoutSaving"
      @save-and-leave="saveAndLeave"
      @update:show-terminal="showTerminal = $event"
      @update:show-test-modal="showTestModal = $event"
      @update:show-grid-edit-dialog="showGridEditDialog = $event"
      @save-grid-ratio="saveGridRatio"
      @update:temp-grid-values="tempGridValues = $event"
      @execute-confirm="executeConfirm"
      @cancel-confirm="cancelConfirm"
      @update:show-create-template-modal="showCreateTemplateModal = $event"
      @inline-template-created="handleInlineTemplateCreated"
      @template-editor-save="handleTemplateEditorSave"
      @template-editor-close="handleTemplateEditorClose"
      @close-toast="toast.show = false"
      @close-module-selector="closeModuleSelector"
      @module-select="handleModuleSelect"
      @update:show-upgrade-modal="showUpgradeModal = $event"
    />

    <!-- Hidden file input for import (bound to composable ref) -->
    <input
      ref="importFileInput"
      type="file"
      :accept="activeTab === 'ui' ? '.json' : '.yaml,.yml'"
      @change="handleImportFile"
      class="hidden"
    />

    <!-- Tab bar -->
    <BuilderTabBar
      v-model:active-tab="activeTab"
      :show-terminal="showTerminal"
      :is-workflow-locked="isWorkflowLocked"
      @toggle-terminal="showTerminal = true"
    />

    <!-- Canvas Area (Error Banner + UI Design + Breadcrumbs + Workflow) -->
    <BuilderCanvas
      ref="builderCanvasRef"
      :active-tab="activeTab"
      :load-error="loadError"
      :sections="templateData.ui.sections"
      :selected-section="selectedSection"
      :selected-column="selectedColumn"
      :selected-component-location="selectedComponentLocation"
      :selected-component-obj="selectedComponentObj"
      :show-layout-picker="showLayoutPicker"
      :show-properties-panel="showPropertiesPanel"
      :current-depth="currentDepth"
      :breadcrumbs="subflowBreadcrumbs"
      :is-workflow-locked="isWorkflowLocked"
      :display-elements="displayElements"
      :selected-node="selectedWorkflowNode"
      :default-modules="defaultModulesList"
      :expert-modules="expertModulesList"
      :debug-mode="debugMode"
      :debug-selected-node-ids="debugSelectedNodeIds"
      :execution-node-states="executionNodeStates"
      :agent-activity="agentActivity"
      :collapsed="nodePropertiesCollapsed"
      :ui-input-fields="uiInputFields"
      :previous-steps="previousSteps"
      :modules-metadata="modulesMetadata"
      :read-only="isReadOnly"
      :checkpoints="builderStore.checkpoints"
      :can-use-checkpoint="hasHumanCheckpoint"
      :can-use-data-pinning="hasDataPinning"
      :execution-status="executionStatus"
      :control-loading="controlStore.loading"
      :saved-viewport="builderStore.viewport"
      @clear-load-error="loadError = null"
      @add-component="addComponentToColumn"
      @toggle-layout-picker="showLayoutPicker = !showLayoutPicker"
      @add-section="openColumnRatioDialog"
      @toggle-properties="showPropertiesPanel = !showPropertiesPanel"
      @select-column="selectColumn"
      @edit-grid="openEditGridDialog"
      @move-section-up="moveSectionUp"
      @move-section-down="moveSectionDown"
      @delete-section="deleteSection"
      @select-component="selectComponent"
      @delete-component="deleteComponent"
      @duplicate-component="duplicateComponent"
      @open-properties="showPropertiesPanel = true"
      @close-properties="showPropertiesPanel = false"
      @update-component="handleComponentUpdate"
      @navigate-breadcrumb="navigateToBreadcrumb"
      @navigate-up="handleNavigateUp"
      @navigate-root="handleNavigateRoot"
      @update:display-elements="displayElements = $event"
      @update:viewport="builderStore.setViewport"
      @node-click="onWorkflowNodeClick"
      @drop="onWorkflowDrop"
      @dragover="onWorkflowDragOver"
      @add-first-node="handleAddFirstNode"
      @delete-node="handleWorkflowNodeDelete"
      @debug-selection-change="onDebugSelectionChange"
      @toggle-collapsed="nodePropertiesCollapsed = !nodePropertiesCollapsed"
      @toggle-checkpoint="handleToggleCheckpoint"
      @pause-execution="handlePause"
      @resume-execution="handleResume"
      @step-execution="handleStep"
      @stop-execution="handleStop"
      @run-to-end="handleRunToEnd"
      @edit-container="handleContainerEdit"
      @retry-node="handleRetryFromNode"
      @create-template="showCreateTemplateModal = true"
      @edit-template="handleEditTemplate"
    />

    <!-- All Overlays & Side Panels -->
    <BuilderOverlays
      :show-resume-panel="showResumePanel"
      :failure-info="controlStore.failureInfo"
      :checkpoints="controlStore.checkpoints"
      :recommended-checkpoint="controlStore.recommendedCheckpoint"
      :control-loading="controlStore.loading"
      :is-paused-at-checkpoint="controlStore.isPausedAtCheckpoint"
      :checkpoint-progress="controlStore.checkpointProgress"
      :show-browser-panel="showBrowserPanel"
      :execution-id="currentExecutionId || ''"
      :user-id="userStore.user?.uid || ''"
      :user-name="userStore.user?.displayName || 'Anonymous'"
      :cloud-mode="isCloudExecution"
      :active-debug-panel="activeDebugPanel"
      :timeline-nodes="timelineNodes"
      :show-settings-panel="showSettingsPanel"
      :template-name="templateName"
      :template-id="templateId"
      :template-description="templateDescription"
      :existing-template-id="existingTemplateId"
      :error-handling="errorHandling"
      :screenshot-mode="screenshotMode"
      :available-workflows="availableWorkflows"
      :selected-step-id="selectedWorkflowNode?.id"
      :workflow-id="templateId"
      :workflow-name="templateName"
      :workflow-steps="workflowSteps"
      :used-modules="usedModules"
      :execution-history="executionHistory"
      :is-loading-history="isLoadingHistory"
      :show-collaboration-panel="showCollaborationPanel"
      :show-invite-modal="showInviteModal"
      :collaboration-session-id="collaborationStore.sessionId || ''"
      :collaboration-participants="collaborationStore.participants"
      :current-user-id="userStore.user?.uid"
      :collaboration-is-connected="collaborationStore.isConnected"
      :collaboration-is-connecting="collaborationStore.isConnecting"
      :collaboration-error="collaborationStore.error"
      :collaboration-is-owner="collaborationStore.isOwner"
      :collaboration-quota-info="collaborationStore.quotaInfo"
      :collaboration-chat-messages="collaborationStore.chatMessages"
      :is-pro="capabilitiesStore.isPro"
      @dismiss-resume-panel="dismissResumePanel"
      @resume-from-checkpoint="handleResumeFromCheckpoint"
      @retry-execution="handleRetryExecution"
      @continue-from-checkpoint="handleContinueFromCheckpoint"
      @bypass-checkpoint="handleBypassCheckpoint"
      @update:show-browser-panel="showBrowserPanel = $event"
      @browser-closed="hasBrowser = false"
      @close-debug-panel="activeDebugPanel = null"
      @timeline-node-select="handleTimelineNodeSelect"
      @update:show-settings-panel="showSettingsPanel = $event"
      @update:template-name="templateName = $event"
      @update:template-id="templateId = $event"
      @update:template-description="templateDescription = $event"
      @update:error-handling="errorHandling = $event"
      @update:screenshot-mode="screenshotMode = $event"
      @settings-import="handleSettingsImport"
      @settings-export="handleSettingsExport"
      @lineage-node-select="handleLineageNodeSelect"
      @replay-started="handleReplayStarted"
      @tests-completed="handleTestsCompleted"
      @version-lock-changed="handleVersionLockChanged"
      @select-execution="handleSelectExecution"
      @replay-execution="handleReplayExecution"
      @stop-execution="handleStopExecution"
      @update:show-collaboration-panel="showCollaborationPanel = $event"
      @show-invite-modal="showInviteModal = true"
      @send-chat="collaborationStore.sendChatMessage($event)"
      @terminate-collaboration="handleTerminateCollaboration"
      @update:show-invite-modal="showInviteModal = $event"
      @show-upgrade-from-invite="showUpgradeModal = true; showInviteModal = false"
    />

    </template>
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { useBuilderStore } from '../stores/builderStore'
import { useModulesStore } from '../stores/modulesStore'
import { backendStepsToElementsAsync } from '../utils/converter/asyncConverter'
import { iconMap } from '../utils/iconMap'

// Composables
import { useWorkflowVisualEditor } from '../composables/workflowEditor/useWorkflowVisualEditor'
import { usePreviousSteps } from '../composables/workflowEditor/usePreviousSteps'
import { useTemplateExecution } from '../composables/templateBuilder/useTemplateExecution'
import { useNotifications } from '../composables/templateBuilder/useNotifications'
import { useSectionManager } from '../composables/templateBuilder/useSectionManager'
import { useComponentManager } from '../composables/templateBuilder/useComponentManager'
import { useTemplateImportExport } from '../composables/templateBuilder/useTemplateImportExport'
import { useTemplateSave } from '../composables/templateBuilder/useTemplateSave'
import { useTemplateLoad } from '../composables/templateBuilder/useTemplateLoad'
import { useDebugPanels } from '../composables/templateBuilder/useDebugPanels'
import { useWorkflowExecution } from '../composables/templateBuilder/useWorkflowExecution'
import { useBuilderState } from '../composables/templateBuilder/useBuilderState'
import { useSubflowTabs } from '../composables/useSubflowTabs'
import { useSubflowElements } from '../composables/templateBuilder/useSubflowElements'
import { useBuilderKeyboardShortcuts } from '../composables/templateBuilder/useBuilderKeyboardShortcuts'
import { useUIInputFields } from '../composables/templateBuilder/useUIInputFields'
import { useBuilderSession } from '../composables/templateBuilder/useBuilderSession'
import { useTemplateEditor } from '../composables/templateBuilder/useTemplateEditor'
import { useBuilderLifecycle } from '../composables/templateBuilder/useBuilderLifecycle'

// Core components
import { BuilderHeader, BuilderTabBar, BuilderSkeleton } from '../components/templateBuilder'
import BuilderDialogs from '../components/templateBuilder/BuilderDialogs.vue'
import BuilderCanvas from '../components/templateBuilder/BuilderCanvas.vue'
import RecordingPanel from '../components/templateBuilder/RecordingPanel.vue'
const BuilderOverlays = defineAsyncComponent(() => import('../components/templateBuilder/BuilderOverlays.vue'))

const { t } = useI18n()
const builderStore = useBuilderStore()
const modulesStore = useModulesStore()

// Recording
import { useRecordingStore } from '../stores/recordingStore'
const recordingStore = useRecordingStore()

const {
  isExecuting, currentExecutionId, executionStatus, executionNodeStates,
  executionNodeTimings, debugMode, debugSelectedNodeIds, controlStore, agentActivity,
  toggleDebugMode, onDebugSelectionChange,
  runWorkflow: executeWorkflow, stopExecution: stopWorkflowExecution,
  pauseExecution, resumeExecution, stepExecution, runToEndExecution,
  resumeFromCheckpoint, screenshotMode, hasBrowser, startExecutionPolling
} = useTemplateExecution()

const { confirmDialog, toast, showConfirm, executeConfirm, cancelConfirm, showToast } = useNotifications()

const {
  elements, selectedNode: selectedWorkflowNode,
  onDragOver: onWorkflowDragOver, onDrop: onWorkflowDrop,
  onNodeClick: onWorkflowNodeClick, createNodeFromModule
} = useWorkflowVisualEditor()

const {
  activeTab, showTerminal, templateName, templateId, templateDescription,
  existingTemplateId, templateCreatorId, templateMutability, templateVisibility,
  templateListed, isWorkflowVisible, hasUnsavedChanges, isSaving,
  isLoadingTemplate, loadError, sections, autoSaveEnabled,
  showLayoutPicker, showGridEditDialog, showPropertiesPanel, showSaveDialog,
  showTestModal, showSettingsPanel, nodePropertiesCollapsed,
  selectedSection, selectedColumn, selectedComponentLocation,
  templateData, selectedComponentObj
} = useBuilderState()

const {
  activeTab: activeSubflowTab, currentFlowId, currentDepth,
  breadcrumbs: subflowBreadcrumbs, openSubflow, navigateToBreadcrumb,
} = useSubflowTabs({
  rootFlowId: computed(() => templateId.value || 'root'),
  rootFlowName: computed(() => templateName.value || 'Main Flow')
})

const { displayElements, initSubflowElements } = useSubflowElements({
  elements, currentDepth, currentFlowId, activeSubflowTab, subflowBreadcrumbs
})

const {
  activeDebugPanel, testStatus, lockedVersionCount, executionCount,
  showDebugToolbar, usedModules, workflowSteps,
  handleToggleDebugPanel, handleLineageNodeSelect, handleReplayStarted,
  handleTestsCompleted, handleVersionLockChanged
} = useDebugPanels({ debugMode, currentExecutionId, elements, onWorkflowNodeClick, showToast })

const showModuleSelector = computed({
  get: () => builderStore.showModuleSelector,
  set: (v) => { builderStore.showModuleSelector = v }
})

const {
  availableSteps, moduleCategories, isLoading: isLoadingModules,
  modulesMetadata, defaultModulesList, expertModulesList
} = storeToRefs(modulesStore)

const {
  tempGridValues, openColumnRatioDialog, openEditGridDialog, saveGridRatio,
  selectColumn, moveSectionUp, moveSectionDown, deleteSection
} = useSectionManager({
  sections, selectedSection, selectedColumn, selectedComponentLocation,
  hasUnsavedChanges, showLayoutPicker, showGridEditDialog, showConfirm, showToast
})

const {
  addComponentToColumn, selectComponent, deleteComponent,
  duplicateComponent, handleComponentUpdate
} = useComponentManager({
  sections, selectedSection, selectedColumn, selectedComponentLocation,
  showPropertiesPanel, hasUnsavedChanges, showConfirm, showToast
})

const builderCanvasRef = ref(null)
const showBrowserPanel = ref(false)
const errorHandling = ref({ onFailure: 'none', errorWorkflowId: null, passErrorContext: true })
const availableWorkflows = ref([])

const {
  importFileInput, triggerImport, handleImportFile, handleExport,
} = useTemplateImportExport({
  elements, templateId, templateName, templateDescription, sections, activeTab,
  modulesMetadata, checkpoints: builderStore.checkpoints, showToast,
  onAutoLayout: () => builderCanvasRef.value?.autoLayout?.()
})

const {
  saveTemplate, saveAsNewTemplate, autoSave, handleBack,
  leaveWithoutSaving, saveAndLeave
} = useTemplateSave({
  elements, sections, templateData, templateName, existingTemplateId,
  templateVisibility, templateListed, viewport: computed(() => builderStore.viewport),
  errorHandling, checkpoints: computed(() => builderStore.checkpoints),
  hasUnsavedChanges, isSaving, showSaveDialog, showToast
})

const { loadExistingTemplate } = useTemplateLoad({
  isLoadingTemplate, loadError, existingTemplateId, templateName, templateId,
  templateDescription, templateCreatorId, templateMutability, templateVisibility,
  templateListed, isWorkflowVisible, sections, elements,
  viewport: computed({ get: () => builderStore.viewport, set: (v) => builderStore.setViewport(v) }),
  activeTab, hasUnsavedChanges, errorHandling, modulesMetadata, iconMap, showToast
})

const {
  executionHistory, isLoadingHistory, handleSelectExecution,
  handleReplayExecution: handleReplayExecutionBase, handleStopExecution,
  handleRetryFromNode, trackSessionStart, trackSessionEnd
} = useBuilderSession({
  elements, existingTemplateId, currentExecutionId, isExecuting,
  executionStatus, controlStore, startExecutionPolling, screenshotMode,
  activeDebugPanel, builderStore, showToast,
  t
})

function handleReplayExecution(execution) {
  const result = handleReplayExecutionBase(execution)
  handleReplayStarted(result)
}

// ===== Workflow Execution =====
const {
  runWorkflow, stopExecution, handlePause, handleStep, handleStop, handleResume,
  handleRunToEnd, handleResumeFromCheckpoint, handleRetryExecution,
  dismissResumePanel, handleToggleCheckpoint, handleContinueFromCheckpoint,
  handleBypassCheckpoint
} = useWorkflowExecution({
  elements, templateId, templateName, templateData, builderStore,
  executeWorkflow, stopWorkflowExecution, pauseExecution, stepExecution,
  resumeExecution, runToEndExecution, resumeFromCheckpoint, controlStore, showToast
})

// ===== Recording =====
async function handleStartRecording() {
  try {
    await recordingStore.startRecording()
  } catch {
    showToast(t('templateBuilder.recording.startFailed', 'Failed to start recording'), 'error')
  }
}

async function handleStopRecording() {
  await recordingStore.stopRecording()
}

async function handleApplyRecording() {
  const workflow = recordingStore.workflowResult
  if (!workflow?.steps?.length) return
  const warningCount = recordingStore.compileWarnings?.length || 0

  try {
    const getModuleById = (moduleId) => modulesMetadata.value[moduleId]
    const { nodes, edges } = await backendStepsToElementsAsync(workflow.steps, {
      getModuleById,
      iconMap,
    })

    elements.value = [...nodes, ...edges]
    if (workflow.name) templateName.value = workflow.name
    builderCanvasRef.value?.autoLayout?.()
    if (warningCount > 0) {
      showToast(
        t('templateBuilder.recording.appliedWithWarnings', '{count} steps added to canvas; {warningCount} recorded actions skipped', {
          count: nodes.length,
          warningCount,
        }),
        'warning'
      )
    } else {
      showToast(
        t('templateBuilder.recording.applied', '{count} steps added to canvas', { count: nodes.length }),
        'success'
      )
    }
  } catch (e) {
    showToast(e.message || 'Failed to apply recording', 'error')
  }

  recordingStore.reset()
}

// ===== Lifecycle (collaboration, auto-save, handlers, computed, mount/unmount) =====
const lifecycle = useBuilderLifecycle({
  elements, displayElements, templateName, templateId, templateDescription,
  existingTemplateId, templateCreatorId, templateMutability, templateVisibility,
  templateListed, isWorkflowVisible, hasUnsavedChanges, isLoadingTemplate,
  loadError, autoSaveEnabled, activeTab, showSettingsPanel,
  showBrowserPanel, executionStatus, executionNodeTimings, executionNodeStates,
  controlStore, hasBrowser, screenshotMode, debugMode, currentExecutionId,
  isExecuting, startExecutionPolling, toggleDebugMode,
  autoSave, showToast, triggerImport, handleExport, loadExistingTemplate,
  trackSessionStart, trackSessionEnd, activeDebugPanel, handleReplayStarted,
  builderStore, builderCanvasRef, selectedWorkflowNode, onWorkflowNodeClick,
  createNodeFromModule, subflowBreadcrumbs, navigateToBreadcrumb, openSubflow,
  initSubflowElements, modulesMetadata,
  errorHandling, availableWorkflows,
})

const {
  isPageReady, showCollaborationPanel, showInviteModal, showUpgradeModal,
  testResult, isCloudExecution,
  showResumePanel, isReadOnly, timelineNodes,
  handleToggleAutoSave, handleToggleSettings, handleTidyNodes,
  handleSettingsImport, handleSettingsExport, handleTerminateCollaboration,
  handleTimelineNodeSelect, handleAddFirstNode, handleModuleSelect,
  closeModuleSelector, handleWorkflowNodeDelete, handleContainerEdit,
  handleNavigateUp, handleNavigateRoot, reloadAvailableModules,
  userStore, capabilitiesStore, collaborationStore,
} = lifecycle

// ===== Workflow Locked =====
const isWorkflowLocked = computed(() => {
  if (!existingTemplateId.value) return false
  if (collaborationStore.isConnected) return false
  return !isWorkflowVisible.value
})

// ===== Template Editor (after lifecycle for reloadAvailableModules) =====
const {
  showCreateTemplateModal, showTemplateEditor, editingTemplate,
  handleEditTemplate, handleTemplateEditorSave, handleTemplateEditorClose,
  handleInlineTemplateCreated,
} = useTemplateEditor({
  elements, hasUnsavedChanges, createNodeFromModule, selectedWorkflowNode,
  showToast, t,
  reloadAvailableModules, defaultModulesList, expertModulesList,
})

// ===== Pro Features =====
const hasHumanCheckpoint = computed(() => capabilitiesStore.hasHumanCheckpoint)
const hasDataPinning = computed(() => capabilitiesStore.hasDataPinning)

// ===== Keyboard Shortcuts =====
useBuilderKeyboardShortcuts({
  activeTab, selectedComponentLocation, selectedWorkflowNode, sections, elements,
  deleteComponent, duplicateComponent, saveTemplate, showToast,
  deleteNode: (nodeId) => {
    const node = elements.value.find(el => el.id === nodeId && !el.source)
    if (node) {
      const nodeType = node.data?.module || 'unknown'
      elements.value = elements.value.filter(el => el.id !== nodeId && el.source !== nodeId && el.target !== nodeId)
      handleWorkflowNodeDelete({ deletedNodes: [nodeId], deletedNodeTypes: [nodeType] })
    }
  }
})

const previousSteps = usePreviousSteps(elements, selectedWorkflowNode)
const { uiInputFields } = useUIInputFields({ sections: templateData })
</script>

<style scoped>
.template-builder-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0f172a;
}
.hidden { display: none; }
</style>
