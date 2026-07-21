<template>
  <Teleport to="body">
    <Transition name="editor-modal">
      <div
        v-if="show"
        class="fixed inset-0 z-[1100] flex flex-col bg-gray-950"
        @keydown.esc="handleBack"
      >
        <!-- Header -->
        <div class="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-gray-900/80 shrink-0">
          <button
            aria-label="Back"
            class="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors"
            @click="handleBack"
          >
            <ArrowLeft :size="16" />
            <span>Back</span>
          </button>

          <div class="h-4 w-px bg-white/15" />

          <!-- Breadcrumb navigation for nested templates -->
          <div class="flex-1 flex items-center gap-1 min-w-0 overflow-x-auto">
            <template v-for="(crumb, index) in breadcrumbs" :key="crumb.templateId">
              <ChevronRight v-if="index > 0" :size="12" class="text-gray-600 shrink-0" />
              <button
                v-if="index < breadcrumbs.length - 1"
                class="text-xs text-gray-400 hover:text-purple-300 transition-colors truncate max-w-[120px] shrink-0"
                @click="navigateToCrumb(index)"
              >
                {{ crumb.name }}
              </button>
              <span v-else class="text-sm font-semibold text-white truncate">
                {{ crumb.name }}
              </span>
            </template>

            <span
              v-if="currentMutability === 'locked'"
              class="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded-full shrink-0 ml-2"
            >
              <Lock :size="12" />
              Locked
            </span>
            <span
              v-else-if="currentMutability === 'fork_on_use'"
              class="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full shrink-0 ml-2"
            >
              <GitFork :size="12" />
              Fork on edit
            </span>
          </div>

          <!-- Tab switcher -->
          <div class="editor-tabs">
            <button
              class="editor-tab"
              :class="{ active: editorTab === 'workflow' }"
              @click="editorTab = 'workflow'"
            >
              <Workflow :size="14" />
              Workflow
            </button>
            <button
              class="editor-tab"
              :class="{ active: editorTab === 'design' }"
              @click="editorTab = 'design'"
            >
              <LayoutDashboard :size="14" />
              UI Design
            </button>
          </div>

          <button
            v-if="!currentReadOnly"
            class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
            :disabled="saving || !dirty"
            @click="handleSave"
          >
            {{ saving ? 'Saving...' : 'Save' }}
          </button>
        </div>

        <!-- Fork banner -->
        <div
          v-if="currentMutability === 'fork_on_use' && !currentReadOnly"
          class="px-4 py-2 bg-blue-500/10 border-b border-blue-500/20 text-blue-300 text-xs flex items-center gap-2 shrink-0"
        >
          <GitFork :size="14" />
          Editing will create a copy of this template.
        </div>

        <!-- Loading -->
        <div v-if="innerLoading || loading" class="flex-1 flex items-center justify-center">
          <div class="flex flex-col items-center gap-3">
            <div class="w-10 h-10 rounded-full border-2 border-transparent border-t-purple-500 animate-spin" />
            <p class="text-sm text-gray-400">Loading template...</p>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="innerError || error" class="flex-1 flex items-center justify-center">
          <div class="text-center">
            <AlertCircle :size="32" class="text-red-400 mx-auto mb-2" />
            <p class="text-sm text-red-400">{{ innerError || error }}</p>
          </div>
        </div>

        <!-- Workflow Tab -->
        <div v-else-if="editorTab === 'workflow'" class="editor-body">
          <WorkflowTab
            :elements="localElements"
            :selected-node="selectedNode"
            :default-modules="defaultModules"
            :expert-modules="expertModules"
            :read-only="currentReadOnly"
            :collapsed="panelCollapsed"
            :modules-metadata="modulesMetadata"
            @update:elements="onElementsUpdate"
            @node-click="onNodeClick"
            @toggle-collapsed="panelCollapsed = !panelCollapsed"
            @delete-node="onDeleteNode"
            @edit-template="onEditNestedTemplate"
          />
        </div>

        <!-- UI Design Tab -->
        <div v-else-if="editorTab === 'design'" class="editor-body">
          <UIDesignTab
            :sections="localSections"
            :selected-section="selectedSection"
            :selected-column="selectedColumn"
            :selected-component-location="selectedComponentLocation"
            :selected-component-obj="selectedComponentObj"
            :show-layout-picker="showLayoutPicker"
            :show-properties-panel="showPropertiesPanel"
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
          />
        </div>

        <!-- Confirm dialog for UI design operations -->
        <ConfirmDialog
          v-if="confirmDialog.show"
          :show="confirmDialog.show"
          :title="confirmDialog.title"
          :message="confirmDialog.message"
          :confirm-text="confirmDialog.confirmText"
          :cancel-text="confirmDialog.cancelText"
          :variant="confirmDialog.type || 'warning'"
          @confirm="executeConfirm"
          @cancel="cancelConfirm"
        />

        <!-- Grid edit dialog for section layout -->
        <GridEditDialog
          :show="showGridEditDialog"
          :grid-values="tempGridValues"
          @save="saveGridRatio"
          @close="showGridEditDialog = false"
        />
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ArrowLeft, Lock, GitFork, AlertCircle, Workflow, LayoutDashboard, ChevronRight } from 'lucide-vue-next'
import WorkflowTab from '@/components/templateBuilder/WorkflowTab.vue'
import UIDesignTab from '@/components/templateBuilder/UIDesignTab.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import GridEditDialog from '@/components/templateBuilder/GridEditDialog.vue'
import { useSectionManager } from '@/composables/templateBuilder/useSectionManager'
import { useComponentManager } from '@/composables/templateBuilder/componentManager'
import { useNotifications } from '@/composables/templateBuilder/useNotifications'
import { templatesAPI } from '@/api/templates'

const props = defineProps({
  show:            { type: Boolean, default: false },
  templateName:    { type: String, default: '' },
  templateId:      { type: String, default: null },
  mutability:      { type: String, default: 'editable' },
  elements:        { type: Array, default: () => [] },
  templateUi:      { type: Object, default: () => ({ sections: [] }) },
  defaultModules:  { type: Array, default: () => [] },
  expertModules:   { type: Array, default: () => [] },
  modulesMetadata: { type: Object, default: () => ({}) },
  readOnly:        { type: Boolean, default: false },
  loading:         { type: Boolean, default: false },
  saving:          { type: Boolean, default: false },
  error:           { type: String, default: null },
  // Step converter functions (passed from parent TemplateBuilder)
  backendStepsToElements: { type: Function, default: null }
})

const emit = defineEmits(['close', 'save'])

// Active editor tab
const editorTab = ref('workflow')

// ===== Nested Template Stack =====
// Each entry: { templateId, name, mutability, elements, sections, dirty }
const templateStack = ref([])
const innerLoading = ref(false)
const innerError = ref(null)

// Breadcrumbs: root template + nested stack
const breadcrumbs = computed(() => {
  const crumbs = [{ templateId: props.templateId, name: props.templateName || 'Template' }]
  for (const entry of templateStack.value) {
    crumbs.push({ templateId: entry.templateId, name: entry.name })
  }
  return crumbs
})

// Current template context (top of stack or root)
const isNested = computed(() => templateStack.value.length > 0)
const currentEntry = computed(() =>
  isNested.value ? templateStack.value[templateStack.value.length - 1] : null
)
const currentMutability = computed(() =>
  currentEntry.value?.mutability || props.mutability
)
const currentReadOnly = computed(() =>
  currentMutability.value === 'locked' || props.readOnly
)

// ===== Workflow State =====
const localElements = ref([])
const selectedNode = ref(null)
const panelCollapsed = ref(false)
const dirty = ref(false)

// ===== UI Design State =====
const localSections = ref([])
const selectedSection = ref(null)
const selectedColumn = ref(null)
const selectedComponentLocation = ref(null)
const showLayoutPicker = ref(false)
const showPropertiesPanel = ref(false)
const showGridEditDialog = ref(false)
const hasUnsavedChanges = dirty

// Notifications
const { confirmDialog, showConfirm, executeConfirm, cancelConfirm, showToast } = useNotifications()

// Computed: selected component object
const selectedComponentObj = computed(() => {
  const loc = selectedComponentLocation.value
  if (!loc) return null
  const section = localSections.value[loc.sectionIndex]
  if (!section) return null
  const column = section.columns?.[loc.columnIndex]
  if (!column) return null
  return column.components?.[loc.componentIndex] || null
})

// ===== Section Manager =====
const {
  editingSectionIndex,
  tempGridValues,
  openColumnRatioDialog,
  openEditGridDialog,
  saveGridRatio,
  selectColumn,
  moveSectionUp,
  moveSectionDown,
  deleteSection
} = useSectionManager({
  sections: localSections,
  selectedSection,
  selectedColumn,
  selectedComponentLocation,
  hasUnsavedChanges,
  showLayoutPicker,
  showGridEditDialog,
  showConfirm,
  showToast
})

// ===== Component Manager =====
const {
  addComponentToColumn,
  selectComponent,
  deleteComponent,
  duplicateComponent,
  handleComponentUpdate
} = useComponentManager({
  sections: localSections,
  selectedSection,
  selectedColumn,
  selectedComponentLocation,
  showPropertiesPanel,
  hasUnsavedChanges,
  showConfirm,
  showToast
})

// ===== State management helpers =====
function resetDesignState() {
  selectedNode.value = null
  panelCollapsed.value = false
  editorTab.value = 'workflow'
  selectedSection.value = null
  selectedColumn.value = null
  selectedComponentLocation.value = null
  showLayoutPicker.value = false
  showPropertiesPanel.value = false
}

function saveCurrentToStack() {
  // Save current state before drilling into nested template
  if (isNested.value) {
    const entry = currentEntry.value
    entry.elements = [...localElements.value]
    entry.sections = JSON.parse(JSON.stringify(localSections.value))
    entry.dirty = dirty.value
  }
  // Root level state is managed by props (parent owns it)
}

function restoreFromEntry(entry) {
  localElements.value = entry ? [...entry.elements] : (props.elements ? [...props.elements] : [])
  localSections.value = entry ? JSON.parse(JSON.stringify(entry.sections)) : (props.templateUi?.sections ? JSON.parse(JSON.stringify(props.templateUi.sections)) : [])
  dirty.value = entry ? entry.dirty : false
  resetDesignState()
}

// ===== Sync from parent =====
watch(() => props.elements, (next) => {
  if (!isNested.value) {
    localElements.value = next ? [...next] : []
    dirty.value = false
    selectedNode.value = null
  }
}, { immediate: true })

watch(() => props.templateUi, (next) => {
  if (!isNested.value) {
    localSections.value = next?.sections ? JSON.parse(JSON.stringify(next.sections)) : []
  }
}, { immediate: true })

// Reset when dialog closes
watch(() => props.show, (open) => {
  if (!open) {
    templateStack.value = []
    dirty.value = false
    innerLoading.value = false
    innerError.value = null
    resetDesignState()
  }
})

// ===== Handlers =====
function onNodeClick(event) {
  selectedNode.value = event?.node || event
}

function onElementsUpdate(next) {
  localElements.value = next
  dirty.value = true
}

function onDeleteNode({ deletedNodes }) {
  if (selectedNode.value && deletedNodes?.includes(selectedNode.value.id)) {
    selectedNode.value = null
  }
  dirty.value = true
}

// ===== Nested template navigation =====
async function onEditNestedTemplate({ templateId }) {
  if (!templateId) return

  // Save current state to stack
  saveCurrentToStack()

  innerLoading.value = true
  innerError.value = null

  try {
    const result = await templatesAPI.getTemplate(templateId)
    if (!result.ok) {
      innerError.value = result.error || 'Failed to load template'
      return
    }
    const tpl = result.template
    const name = tpl.name || tpl.templateName || 'Template'
    const mut = tpl.mutability || 'editable'
    const steps = tpl.steps || tpl.workflowSteps || []
    const ui = tpl.ui || { sections: [] }

    let elements = []
    if (steps.length > 0 && props.backendStepsToElements) {
      const converted = await props.backendStepsToElements(steps)
      elements = [...converted.nodes, ...converted.edges]
    }

    // Push onto stack
    templateStack.value.push({
      templateId,
      name,
      mutability: mut,
      elements,
      sections: ui.sections ? JSON.parse(JSON.stringify(ui.sections)) : [],
      dirty: false,
      template: tpl
    })

    // Load into editor
    localElements.value = elements
    localSections.value = ui.sections ? JSON.parse(JSON.stringify(ui.sections)) : []
    dirty.value = false
    resetDesignState()
  } catch (err) {
    console.error('Failed to load nested template:', err)
    innerError.value = 'Failed to load template'
  } finally {
    innerLoading.value = false
  }
}

function navigateToCrumb(index) {
  // index 0 = root template
  // Pop stack entries above the target
  while (templateStack.value.length > index) {
    templateStack.value.pop()
  }

  const entry = templateStack.value.length > 0
    ? templateStack.value[templateStack.value.length - 1]
    : null
  restoreFromEntry(entry)
  innerError.value = null
}

function handleBack() {
  if (isNested.value) {
    // Pop one level
    templateStack.value.pop()
    const entry = templateStack.value.length > 0
      ? templateStack.value[templateStack.value.length - 1]
      : null
    restoreFromEntry(entry)
    innerError.value = null
  } else {
    emit('close')
  }
}

function handleSave() {
  if (isNested.value) {
    // Save nested template: emit to parent for API handling
    const entry = currentEntry.value
    emit('save', {
      templateId: entry.templateId,
      mutability: entry.mutability,
      elements: localElements.value,
      ui: { sections: localSections.value },
      isNested: true
    })
  } else {
    emit('save', {
      elements: localElements.value,
      ui: { sections: localSections.value }
    })
  }
}
</script>

<style scoped>
.editor-body {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

/* Tab switcher */
.editor-tabs {
  display: flex;
  gap: 2px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 2px;
  shrink: 0;
}

.editor-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #94A3B8;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.editor-tab:hover {
  color: #E2E8F0;
  background: rgba(255, 255, 255, 0.05);
}

.editor-tab.active {
  color: #A78BFA;
  background: rgba(139, 92, 246, 0.15);
}

.editor-modal-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.editor-modal-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 1, 1);
}
.editor-modal-enter-from,
.editor-modal-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
