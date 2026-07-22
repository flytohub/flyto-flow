<template>
  <!-- Load Error Banner -->
  <div v-if="loadError" class="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg mx-4 mt-4 flex items-center gap-3">
    <AlertCircle :size="20" class="flex-shrink-0" />
    <div class="flex-1">
      <p class="font-medium">{{ $t('templateBuilder.messages.loadTemplateFailed') }}</p>
      <p class="text-sm opacity-80">{{ loadError }}</p>
    </div>
    <button @click="$emit('clear-load-error')" class="p-1 hover:bg-red-200 dark:hover:bg-red-800 rounded" aria-label="Dismiss error">
      <X :size="16" />
    </button>
  </div>

  <!-- UI Design Tab -->
  <UIDesignTab
    v-show="activeTab === 'ui'"
    :sections="sections"
    :selected-section="selectedSection"
    :selected-column="selectedColumn"
    :selected-component-location="selectedComponentLocation"
    :selected-component-obj="selectedComponentObj"
    :show-layout-picker="showLayoutPicker"
    :show-properties-panel="showPropertiesPanel"
    @add-component="$emit('add-component', $event)"
    @toggle-layout-picker="$emit('toggle-layout-picker')"
    @add-section="$emit('add-section', $event)"
    @toggle-properties="$emit('toggle-properties')"
    @select-column="(s, c) => $emit('select-column', s, c)"
    @edit-grid="$emit('edit-grid', $event)"
    @move-section-up="$emit('move-section-up', $event)"
    @move-section-down="$emit('move-section-down', $event)"
    @delete-section="$emit('delete-section', $event)"
    @select-component="(s, c, i) => $emit('select-component', s, c, i)"
    @delete-component="(s, c, i) => $emit('delete-component', s, c, i)"
    @duplicate-component="(s, c, i) => $emit('duplicate-component', s, c, i)"
    @open-properties="$emit('open-properties')"
    @close-properties="$emit('close-properties')"
    @update-component="$emit('update-component', $event)"
  />

  <!-- Subflow Breadcrumbs (shown when inside a container subflow) -->
  <SubflowBreadcrumbs
    v-if="activeTab === 'workflow' && currentDepth > 0"
    :breadcrumbs="breadcrumbs"
    @navigate="$emit('navigate-breadcrumb', $event)"
    @navigate-up="$emit('navigate-up')"
    @navigate-root="$emit('navigate-root')"
  />

  <!-- Workflow Tab -->
  <WorkflowTab
    ref="workflowTabRef"
    v-show="activeTab === 'workflow'"
    :elements="displayElements"
    :selected-node="selectedNode"
    :default-modules="defaultModules"
    :expert-modules="expertModules"
    :debug-mode="debugMode"
    :debug-selected-node-ids="debugSelectedNodeIds"
    :execution-node-states="executionNodeStates"
    :agent-activity="agentActivity"
    :collapsed="collapsed"
    :ui-input-fields="uiInputFields"
    :previous-steps="previousSteps"
    :modules-metadata="modulesMetadata"
    :read-only="readOnly"
    :checkpoints="checkpoints"
    :can-use-checkpoint="canUseCheckpoint"
    :can-use-data-pinning="canUseDataPinning"
    :execution-status="executionStatus"
    :control-loading="controlLoading"
    :saved-viewport="savedViewport"
    @update:elements="$emit('update:displayElements', $event)"
    @update:viewport="$emit('update:viewport', $event)"
    @node-click="$emit('node-click', $event)"
    @drop="$emit('drop', $event)"
    @dragover="$emit('dragover', $event)"
    @add-first-node="$emit('add-first-node')"
    @delete-node="$emit('delete-node', $event)"
    @debug-selection-change="$emit('debug-selection-change', $event)"
    @toggle-collapsed="$emit('toggle-collapsed')"
    @toggle-checkpoint="$emit('toggle-checkpoint', $event)"
    @pause-execution="$emit('pause-execution')"
    @resume-execution="$emit('resume-execution')"
    @step-execution="$emit('step-execution')"
    @stop-execution="$emit('stop-execution')"
    @run-to-end="$emit('run-to-end')"
    @edit-container="$emit('edit-container', $event)"
    @retry-node="$emit('retry-node', $event)"
    @create-template="$emit('create-template')"
    @edit-template="$emit('edit-template', $event)"
  />
</template>

<script setup>
import { ref } from 'vue'
import { AlertCircle, X } from 'lucide-vue-next'
import { UIDesignTab, WorkflowTab, SubflowBreadcrumbs } from '../templateBuilder'

defineProps({
  activeTab: { type: String, required: true },
  loadError: { type: String, default: null },
  // UI Design Tab
  sections: { type: Array, default: () => [] },
  selectedSection: { type: Number, default: null },
  selectedColumn: { type: Number, default: null },
  selectedComponentLocation: { type: Object, default: null },
  selectedComponentObj: { type: Object, default: null },
  showLayoutPicker: { type: Boolean, default: false },
  showPropertiesPanel: { type: Boolean, default: false },
  // Subflow Breadcrumbs
  currentDepth: { type: Number, default: 0 },
  breadcrumbs: { type: Array, default: () => [] },
  // Workflow Tab
  displayElements: { type: Array, default: () => [] },
  selectedNode: { type: Object, default: null },
  defaultModules: { type: Array, default: () => [] },
  expertModules: { type: Array, default: () => [] },
  debugMode: { type: Boolean, default: false },
  debugSelectedNodeIds: { type: Array, default: () => [] },
  executionNodeStates: { type: Object, default: () => ({}) },
  agentActivity: { type: Object, default: () => ({}) },
  collapsed: { type: Boolean, default: false },
  uiInputFields: { type: Array, default: () => [] },
  previousSteps: { type: Array, default: () => [] },
  modulesMetadata: { type: Object, default: () => ({}) },
  readOnly: { type: Boolean, default: false },
  checkpoints: { type: Object, default: () => ({}) },
  canUseCheckpoint: { type: Boolean, default: false },
  canUseDataPinning: { type: Boolean, default: false },
  executionStatus: { type: String, default: null },
  controlLoading: { type: Boolean, default: false },
  savedViewport: { type: Object, default: null },
})

defineEmits([
  'clear-load-error',
  // UI Design Tab
  'add-component', 'toggle-layout-picker', 'add-section', 'toggle-properties',
  'select-column', 'edit-grid', 'move-section-up', 'move-section-down',
  'delete-section', 'select-component', 'delete-component', 'duplicate-component',
  'open-properties', 'close-properties', 'update-component',
  // Subflow Breadcrumbs
  'navigate-breadcrumb', 'navigate-up', 'navigate-root',
  // Workflow Tab
  'update:displayElements', 'update:viewport',
  'node-click', 'drop', 'dragover', 'add-first-node', 'delete-node',
  'debug-selection-change', 'toggle-collapsed', 'toggle-checkpoint',
  'pause-execution', 'resume-execution', 'step-execution', 'stop-execution',
  'run-to-end', 'edit-container', 'retry-node', 'create-template', 'edit-template',
])

const workflowTabRef = ref(null)

defineExpose({
  autoLayout: () => workflowTabRef.value?.autoLayout?.()
})
</script>
