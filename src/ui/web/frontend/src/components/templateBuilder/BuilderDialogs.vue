<template>
  <!-- Save confirmation dialog -->
  <SaveConfirmDialog
    :show="showSaveDialog"
    @close="$emit('update:showSaveDialog', false)"
    @leaveWithoutSaving="$emit('leave-without-saving')"
    @saveAndLeave="$emit('save-and-leave')"
  />

  <!-- Terminal Log Dialog -->
  <TerminalLogDialog
    :show="showTerminal"
    @close="$emit('update:showTerminal', false)"
  />

  <!-- Test Modal -->
  <TestModal
    :show="showTestModal"
    :result="testResult"
    @close="$emit('update:showTestModal', false)"
  />

  <!-- Grid Edit Dialog -->
  <GridEditDialog
    :show="showGridEditDialog"
    :grid-values="tempGridValues"
    @close="$emit('update:showGridEditDialog', false)"
    @save="$emit('save-grid-ratio')"
    @update:grid-values="$emit('update:tempGridValues', $event)"
  />

  <!-- Confirm Dialog -->
  <ConfirmDialog
    :show="confirmDialog.show"
    :variant="confirmDialog.type || 'warning'"
    :title="confirmDialog.title"
    :message="confirmDialog.message"
    :confirm-text="confirmDialog.confirmText || $t('common.confirm')"
    :cancel-text="$t('common.cancel')"
    @confirm="$emit('execute-confirm')"
    @cancel="$emit('cancel-confirm')"
  />

  <!-- Create Template Modal (from AddNodeMenu) -->
  <CreateTemplateModal
    v-model="showCreateTemplateModalLocal"
    @created="$emit('inline-template-created', $event)"
  />

  <!-- Template Editor Dialog (workflow + UI design) -->
  <TemplateEditorDialog
    :show="showTemplateEditor"
    :template-id="editingTemplate.id"
    :template-name="editingTemplate.name"
    :mutability="editingTemplate.mutability"
    :elements="editingTemplate.elements"
    :template-ui="editingTemplate.ui"
    :default-modules="defaultModules"
    :expert-modules="expertModules"
    :modules-metadata="modulesMetadata"
    :read-only="editingTemplate.mutability === 'locked'"
    :loading="editingTemplate.loading"
    :saving="editingTemplate.saving"
    :error="editingTemplate.error"
    :backend-steps-to-elements="backendStepsToElements"
    @save="$emit('template-editor-save', $event)"
    @close="$emit('template-editor-close')"
  />

  <!-- Toast Notification -->
  <ToastNotification
    :show="toast.show"
    :type="toast.type"
    :message="toast.message"
    @close="$emit('close-toast')"
  />

  <!-- Module Selector -->
  <ModuleSelector
    :isOpen="showModuleSelector"
    :moduleCategories="moduleCategories"
    :availableSteps="availableSteps"
    :isLoadingModules="isLoadingModules"
    :defaultModules="defaultModules"
    :expertModules="expertModules"
    :isAddingFirstNode="isAddingFirstNode"
    @close="$emit('close-module-selector')"
    @select="$emit('module-select', $event)"
  />

  <!-- Upgrade Modal (for premium feature gating) -->
  <UpgradeModal v-model="showUpgradeModalLocal" />
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'

// Core components (always needed)
import { SaveConfirmDialog, ToastNotification } from '../templateBuilder'
import ConfirmDialog from '../common/ConfirmDialog.vue'
import ModuleSelector from '../ModuleSelector.vue'

// Lazy-loaded components
const TerminalLogDialog = defineAsyncComponent(() => import('../templateBuilder/TerminalLogDialog.vue'))
const GridEditDialog = defineAsyncComponent(() => import('../templateBuilder/GridEditDialog.vue'))
const TestModal = defineAsyncComponent(() => import('../templateBuilder/TestModal.vue'))
const TemplateEditorDialog = defineAsyncComponent(() => import('../templates/TemplateEditorDialog.vue'))
const CreateTemplateModal = defineAsyncComponent(() => import('../templates/CreateTemplateModal.vue'))
const UpgradeModal = defineAsyncComponent(() => import('../common/UpgradeModal.vue'))

const props = defineProps({
  activeTab: { type: String, required: true },
  // Save dialog
  showSaveDialog: { type: Boolean, default: false },
  // Terminal
  showTerminal: { type: Boolean, default: false },
  // Test modal
  showTestModal: { type: Boolean, default: false },
  testResult: { type: Object, default: null },
  // Grid edit
  showGridEditDialog: { type: Boolean, default: false },
  tempGridValues: { type: Array, default: () => [] },
  // Confirm dialog
  confirmDialog: { type: Object, required: true },
  // Create template modal
  showCreateTemplateModal: { type: Boolean, default: false },
  // Template editor
  showTemplateEditor: { type: Boolean, default: false },
  editingTemplate: { type: Object, required: true },
  defaultModules: { type: Array, default: () => [] },
  expertModules: { type: Array, default: () => [] },
  modulesMetadata: { type: Object, default: () => ({}) },
  backendStepsToElements: { type: Function, required: true },
  // Toast
  toast: { type: Object, required: true },
  // Module selector
  showModuleSelector: { type: Boolean, default: false },
  moduleCategories: { type: Array, default: () => [] },
  availableSteps: { type: Array, default: () => [] },
  isLoadingModules: { type: Boolean, default: false },
  isAddingFirstNode: { type: Boolean, default: false },
  // Upgrade modal
  showUpgradeModal: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:showSaveDialog', 'leave-without-saving', 'save-and-leave',
  'update:showTerminal',
  'update:showTestModal',
  'update:showGridEditDialog', 'save-grid-ratio', 'update:tempGridValues',
  'execute-confirm', 'cancel-confirm',
  'update:showCreateTemplateModal', 'inline-template-created',
  'template-editor-save', 'template-editor-close',
  'close-toast',
  'close-module-selector', 'module-select',
  'update:showUpgradeModal',
])

// v-model proxies for components that need v-model
const showCreateTemplateModalLocal = computed({
  get: () => props.showCreateTemplateModal,
  set: (v) => emit('update:showCreateTemplateModal', v)
})

const showUpgradeModalLocal = computed({
  get: () => props.showUpgradeModal,
  set: (v) => emit('update:showUpgradeModal', v)
})

</script>
