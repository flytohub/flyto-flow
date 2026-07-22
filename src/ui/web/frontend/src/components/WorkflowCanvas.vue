<template>
  <div
    class="workflow-canvas-container"
    :class="{ 'debug-mode': debugMode }"
  >
    <!-- SVG filter definitions for edge glow effects (must be in DOM for filter: url(#...) to work) -->
    <div v-html="edgeFilterSvg" style="position:absolute;width:0;height:0;overflow:hidden;pointer-events:none"></div>

    <VueFlow
      v-model:nodes="nodes"
      v-model:edges="edges"
      :edge-types="edgeTypes"
      :default-edge-options="edgeOptions"
      :is-valid-connection="isValidConnection"
      :connection-radius="50"
      :snap-to-grid="true"
      :snap-grid="[20, 20]"
      :selection-key-code="null"
      :multi-selection-key-code="'Shift'"
      :selection-on-drag="true"
      :pan-on-drag="true"
      :selection-mode="'partial'"
      @connect="handleConnect"
      @node-click="handleNodeClick"
      @node-double-click="handleNodeDoubleClick"
      @node-context-menu="handleNodeContextMenuEvent"
      @edge-click="handleEdgeClick"
      @pane-click="handlePaneClick"
      @move-end="handleViewportChange"
      :fit-view-on-init="!props.savedViewport"
      class="workflow-canvas"
    >
      <Background :gap="20" pattern-color="#334155" />

      <!-- MiniMap for navigation -->
      <MiniMap
        class="cyber-minimap"
        position="bottom-right"
        :pannable="true"
        :zoomable="true"
        :width="180"
        :height="120"
        :node-stroke-width="2"
        :node-color="getMinimapNodeColor"
        :node-stroke-color="getMinimapNodeStroke"
        :node-class-name="getMinimapNodeClass"
        mask-color="rgba(139, 92, 246, 0.12)"
        mask-stroke-color="#A855F7"
        :mask-stroke-width="2"
      />

      <!-- Canvas Controls -->
      <CanvasControls
        :can-align="canAlign"
        :can-distribute="canDistribute"
        @zoom-in="handleZoomIn"
        @zoom-out="handleZoomOut"
        @fit-view="handleFitView"
        @auto-layout="handleAutoLayout"
        @align-left="alignLeft"
        @align-right="alignRight"
        @align-top="alignTop"
        @align-bottom="alignBottom"
        @distribute-h="distributeHorizontal"
        @distribute-v="distributeVertical"
      />

      <template #node-custom="nodeProps">
        <WorkflowNode
          :id="nodeProps.id"
          :data="nodeProps.data"
          :selected="nodeProps.id === selectedNodeId"
          :is-first="isFirstNode(nodeProps.id, edges)"
          :has-loop="edges.some(e => e.target === nodeProps.id && e.sourceHandle === 'source-error') ? 'error' : edges.some(e => e.target === nodeProps.id && (e.sourceHandle === 'body_out' || e.data?.edgeType === 'iterate')) ? 'loop' : false"
          :edges="edges"
          :has-checkpoint="checkpoints.includes(nodeProps.id)"
          :node-output="controlStore.getNodeOutput(nodeProps.id)"
          :is-pinned="nodeProps.data?.isPinned || false"
          :compact="nodeProps.data?.collapsed || false"
          @add-node="handleAddNodeRequest"
          @delete-node="handleDeleteNodeRequest"
          @edit-container="handleEditContainer"
          @retry-node="handleRetryNode"
          @replace-node="handleReplaceNodeRequest"
          @edit-template="(e) => emit('edit-template', e)"
          @save-as-template="handleContainerSaveAsTemplate"
        />
      </template>

      <template #node-sticky="nodeProps">
        <StickyNote
          :id="nodeProps.id"
          :data="nodeProps.data"
          :selected="nodeProps.id === selectedNodeId"
          @delete-node="handleDeleteNodeRequest"
          @update-node="handleStickyNoteUpdate"
        />
      </template>

    </VueFlow>

    <!-- Empty State -->
    <EmptyCanvasState
      v-if="nodes.length === 0"
      @add-node="$emit('add-first-node')"
    />

    <!-- Add Node Menu -->
    <AddNodeMenu
      :isOpen="menuOpen"
      :defaultModules="filteredDefaultModules"
      :expertModules="filteredExpertModules"
      :isLoading="isLoadingCompatible"
      :moduleFilter="pendingModuleFilter"
      :isInsertionMode="isInsertionMode"
      :isReplaceMode="isReplaceMode"
      @close="closeMenu"
      @select-module="handleModuleSelected"
      @create-template="closeMenu(); emit('create-template')"
    />

    <!-- Reconnect Confirmation Dialog -->
    <ConfirmDialog
      :show="showReconnectDialog"
      :title="reconnectDialogTitle"
      :message="reconnectDialogMessage"
      :confirm-text="t('workflowCanvas.reconnect.connect')"
      :cancel-text="t('workflowCanvas.reconnect.dontConnect')"
      :secondary-text="t('workflowCanvas.reconnect.cancel')"
      :show-secondary="true"
      variant="primary"
      @confirm="confirmReconnect"
      @cancel="skipReconnect"
      @secondary="cancelDelete"
    />

    <!-- Switch Case Selector -->
    <CaseSelectorModal
      :show="showCaseSelector"
      :case-options="pendingCaseOptions"
      @select="confirmCaseSelection"
      @cancel="cancelCaseSelection"
    />

    <!-- Delete with children dialog -->
    <DeleteChildrenDialog
      :show="showDeleteChildrenDialog"
      :child-count="pendingDeleteChildCount"
      @merge="handleMergeToChild"
      @delete-all="handleDeleteAllChildren"
      @cancel="cancelDeleteWithChildren"
    />

    <!-- Node Action Bar -->
    <NodeActionBar
      :selected-node="actionBarNode"
      :checkpoints="checkpoints"
      :can-use-checkpoint="canUseCheckpoint"
      :can-use-data-pinning="canUseDataPinning"
      :has-node-output="hasActionBarNodeOutput"
      @toggle-checkpoint="handleToggleCheckpoint"
      @toggle-pin="handleTogglePin"
      @toggle-disabled="handleToggleDisabled"
      @toggle-collapse="handleToggleCollapse"
      @edit-note="handleEditNote"
      @delete-node="handleActionBarDelete"
      @close="actionBarNode = null"
    />

    <!-- Execution Control Bar -->
    <ExecutionControlBar
      v-if="checkpoints.length > 0"
      :is-running="executionStatus === 'running'"
      :is-paused="executionStatus === 'paused'"
      :loading="controlLoading"
      :has-checkpoints="true"
      @pause="$emit('pause-execution')"
      @resume="$emit('resume-execution')"
      @step="$emit('step-execution')"
      @run-to-end="$emit('run-to-end')"
      @stop="$emit('stop-execution')"
    />

    <!-- Node Search Dialog (Ctrl+F) -->
    <NodeSearchDialog
      :is-open="showNodeSearch"
      :nodes="nodes"
      @close="showNodeSearch = false"
      @select="handleSearchSelect"
    />

    <!-- Note Edit Modal -->
    <NoteEditModal
      :show="showNoteModal"
      :initial-note="noteModalInitialValue"
      @save="handleNoteSave"
      @delete="handleNoteDelete"
      @close="showNoteModal = false"
    />

    <!-- Node Context Menu (Right-click) -->
    <NodeContextMenu
      :visible="contextMenuVisible"
      :position="contextMenuPosition"
      :node="contextMenuNode"
      @close="closeContextMenu"
      @save-as-template="handleSaveAsTemplate"
      @duplicate="handleDuplicateNode"
      @toggle-disabled="handleToggleDisabled"
      @delete="handleActionBarDelete"
    />

    <!-- Save as Template Dialog -->
    <SaveAsTemplateDialog
      v-model="showSaveAsTemplate"
      :node="saveAsTemplateNode"
    />

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, markRaw, nextTick, provide } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { useI18n } from 'vue-i18n'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { MiniMap } from '@vue-flow/minimap'

// Components
import WorkflowNode from './WorkflowNode.vue'
import AddNodeMenu from './AddNodeMenu.vue'
import EmptyCanvasState from './EmptyCanvasState.vue'
import { StickyNote } from './workflowCanvas/nodes'
import { GlowEdge } from './workflowCanvas/edges'
import ConfirmDialog from './common/ConfirmDialog.vue'
import { DeleteChildrenDialog } from './workflowCanvas'
import NodeActionBar from './workflowCanvas/NodeActionBar.vue'
import ExecutionControlBar from './workflowCanvas/ExecutionControlBar.vue'
import NodeSearchDialog from './workflowCanvas/NodeSearchDialog.vue'
import NoteEditModal from './workflowCanvas/NoteEditModal.vue'
import CanvasControls from './workflowCanvas/CanvasControls.vue'
import CaseSelectorModal from './workflowCanvas/CaseSelectorModal.vue'
import NodeContextMenu from './workflowCanvas/NodeContextMenu.vue'
import SaveAsTemplateDialog from './workflowCanvas/SaveAsTemplateDialog.vue'

// Operations and utilities
import {
  EDGE_STYLE,
  EDGE_MARKER,
  filterNodes,
  filterEdges,
} from '../composables/workflowEditor/useCanvasOperations'
import { useAutoLayout } from '../composables/workflowEditor/canvasOps/autoLayout'
import { CASE_COLORS } from '../config/nodeTypes/SwitchNode'
import { getEdgeFilterDefs } from '@/config/edgeDesignSystem'
import { DEFAULTS } from '@/config/defaults'
import { isFirstNode, hasLoopNodes } from '../composables/workflowEditor/useNodeRules'

// Composables
import { useExecutionControlStore } from '../stores/executionControlStore'
import { useNodeOperations } from '../composables/workflowEditor/useNodeOperations'
import { useNodeAlignment } from '../composables/workflowEditor/useNodeAlignment'
import { useDebugSelection } from '../composables/workflowEditor/useDebugSelection'
import { useExecutionState } from '../composables/workflowEditor/useExecutionState'
import { useCanvasHistory, HISTORY_ACTIONS } from '../composables/workflowEditor/useCanvasHistory'
import { useClipboard } from '../composables/workflowEditor/useClipboard'
import { useMinimapStyling } from '../composables/workflowEditor/useMinimapStyling'
import { useCanvasConnections } from '../composables/workflowEditor/useCanvasConnections'
import { useCanvasDialogs } from '../composables/workflowEditor/useCanvasDialogs'
import { useCanvasViewport } from '../composables/workflowEditor/useCanvasViewport'
import { useCanvasEvents } from '../composables/workflowEditor/useCanvasEvents'
import { useToast } from '../composables/useToast'

const props = defineProps({
  elements: { type: Array, default: () => [] },
  defaultModules: { type: Array, default: () => [] },
  expertModules: { type: Array, default: () => [] },
  modulesMetadata: { type: Object, default: () => ({}) },
  selectedNodeId: { type: String, default: null },
  debugMode: { type: Boolean, default: false },
  debugSelectedNodes: { type: Array, default: () => [] },
  executionNodeStates: { type: Object, default: () => ({}) },
  agentActivity: { type: Object, default: () => ({}) },
  checkpoints: { type: Array, default: () => [] },
  canUseCheckpoint: { type: Boolean, default: false },
  canUseDataPinning: { type: Boolean, default: false },
  savedViewport: { type: Object, default: null },
  executionStatus: { type: String, default: 'idle' },
  controlLoading: { type: Boolean, default: false }
})

const emit = defineEmits([
  'update:elements',
  'update:viewport',
  'node-click',
  'delete-node',
  'add-first-node',
  'toggle-checkpoint',
  'pause-execution',
  'resume-execution',
  'step-execution',
  'stop-execution',
  'run-to-end',
  'retry-node',
  'edit-container',
  'create-template',
  'edit-template'
])

// Core utilities
const { t } = useI18n()
const toast = useToast()
const controlStore = useExecutionControlStore()
const { updateNodeInternals } = useVueFlow()
const { layout: autoLayout } = useAutoLayout()

// === Edge SVG Filters (injected once into DOM for glow effects) ===
const edgeFilterSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0"><defs>${getEdgeFilterDefs()}</defs></svg>`

// === Minimap Styling ===
const { getMinimapNodeColor, getMinimapNodeStroke, getMinimapNodeClass } = useMinimapStyling()

// === VueFlow State ===
const nodes = ref([])
const edges = ref([])

// === Canvas History ===
const {
  pushState: historyPushState,
  undo: historyUndo,
  redo: historyRedo,
  canUndo,
  canRedo
} = useCanvasHistory({ maxHistory: 50 })

function saveHistoryState(action, metadata = {}) {
  historyPushState(action, { nodes: nodes.value, edges: edges.value }, metadata)
}

// === Sync ===
// Track the node count at last sync to distinguish "echo" from "external update"
let isSyncing = false
let lastSyncNodeCount = -1
const debouncedSyncEmit = useDebounceFn(() => {
  emit('update:elements', [...nodes.value, ...edges.value])
  isSyncing = false
}, DEFAULTS.TIMING.SYNC_DEBOUNCE)

function syncToParent() {
  lastSyncNodeCount = nodes.value.length
  isSyncing = true
  debouncedSyncEmit()
}

// === Connections (composable) ===
const {
  showCaseSelector,
  pendingCaseOptions,
  isValidConnection,
  handleConnect,
  confirmCaseSelection,
  cancelCaseSelection
} = useCanvasConnections({ nodes, edges, saveHistoryState, syncToParent, HISTORY_ACTIONS })

// === Dialogs (composable) ===
const {
  showNodeSearch,
  showNoteModal,
  noteModalInitialValue,
  handleEditNote,
  handleNoteSave,
  handleNoteDelete
} = useCanvasDialogs({ nodes, syncToParent, saveHistoryState, HISTORY_ACTIONS })

// === Viewport (composable) ===
const {
  handleZoomIn,
  handleZoomOut,
  handleFitView,
  restoreViewport,
  setCenter,
  createViewportChangeHandler
} = useCanvasViewport({ nodes })

const { handleViewportChange, cleanup: cleanupViewportTimer } = createViewportChangeHandler(emit)

// === Clipboard ===
const {
  copySelectedNodes,
  pasteNodes
} = useClipboard({
  nodes,
  edges,
  onSync: syncToParent,
  onBeforePaste: () => saveHistoryState(HISTORY_ACTIONS.NODE_ADD)
})

// === Node Operations (addition + deletion) ===
const {
  menuOpen,
  isLoadingCompatible,
  pendingModuleFilter,
  filterModules,
  openAddNodeMenu,
  openInsertNodeMenu,
  openReplaceNodeMenu,
  isInsertionMode,
  isReplaceMode,
  handleModuleSelected,
  closeMenu,
  showReconnectDialog,
  reconnectDialogTitle,
  reconnectDialogMessage,
  showDeleteChildrenDialog,
  pendingDeleteChildCount,
  handleDeleteEdge,
  requestDeleteNode,
  confirmReconnect,
  skipReconnect,
  cancelDelete,
  handleMergeToChild,
  handleDeleteAllChildren,
  cancelDeleteWithChildren
} = useNodeOperations({
  nodes,
  edges,
  caseColors: CASE_COLORS,
  onSync: syncToParent,
  onBeforeAdd: () => saveHistoryState(HISTORY_ACTIONS.NODE_ADD),
  onDelete: (data) => emit('delete-node', data)
})

const filteredDefaultModules = computed(() => filterModules(props.defaultModules))
const filteredExpertModules = computed(() => filterModules(props.expertModules))

// === Node Alignment ===
const {
  canAlign,
  canDistribute,
  alignLeft,
  alignRight,
  alignTop,
  alignBottom,
  distributeHorizontal,
  distributeVertical
} = useNodeAlignment(nodes, syncToParent, saveHistoryState)

// === Debug Selection ===
const { handleDebugNodeClick } = useDebugSelection(nodes, emit, props)

// === Execution State ===
const { setupExecutionWatcher } = useExecutionState(nodes, edges, props)
setupExecutionWatcher()

// === Canvas Events (composable) ===
const {
  selectedEdgeId,
  actionBarNode,
  hasActionBarNodeOutput,
  contextMenuVisible,
  contextMenuPosition,
  contextMenuNode,
  closeContextMenu,
  showSaveAsTemplate,
  saveAsTemplateNode,
  handleNodeClick,
  handleNodeContextMenuEvent,
  handleEdgeClick,
  handleEdgeInsertNode,
  handleNodeDoubleClick,
  handleToggleCheckpoint,
  handleRetryNode,
  handleEditContainer,
  handleReplaceNodeRequest,
  handleActionBarDelete,
  handleTogglePin,
  handleToggleDisabled,
  handleToggleCollapse,
  handleStickyNoteUpdate,
  handlePaneClick,
  handleAddNodeRequest,
  handleDeleteNodeRequest,
  handleSearchSelect,
  handleSaveAsTemplate,
  handleDuplicateNode,
  handleAutoLayout,
  onKeyDown,
  cleanupArrowKeyTimer,
} = useCanvasEvents({

  nodes,
  edges,
  props,
  emit,
  controlStore,
  toast,
  t,
  updateNodeInternals,
  saveHistoryState,
  syncToParent,
  requestDeleteNode,
  openAddNodeMenu,
  openInsertNodeMenu,
  openReplaceNodeMenu,
  handleDeleteEdge,
  handleDebugNodeClick,
  setCenter,
  menuOpen,
  showCaseSelector,
  cancelCaseSelection,
  showNodeSearch,
  copySelectedNodes,
  pasteNodes,
  handleFitView,
  autoLayout,
  historyUndo: historyUndo,
  historyRedo: historyRedo,
  canUndo,
  canRedo,
})

provide('onEdgeInsertNode', handleEdgeInsertNode)

// Container node "Save as Template" button handler
// Resolves { nodeId } to full node object and delegates to existing handleSaveAsTemplate
function handleContainerSaveAsTemplate({ nodeId }) {
  const node = nodes.value.find(n => n.id === nodeId)
  if (node) handleSaveAsTemplate(node)
}

// === Edge Types ===
const edgeTypes = {
  glow: markRaw(GlowEdge),
  straight: markRaw(GlowEdge),
  smoothstep: markRaw(GlowEdge),
  default: markRaw(GlowEdge)
}

const edgeOptions = {
  type: 'glow',
  style: { ...EDGE_STYLE },
  markerEnd: { ...EDGE_MARKER }
}

// === Init from Props ===
let hasInitialLayout = false

watch(() => props.elements, (elements) => {
  if (!elements) return
  // Only skip echo updates (same node count bouncing back from our own sync).
  // If node count differs, this is an external update (e.g. YAML import) — always process it.
  if (isSyncing) {
    const incomingNodeCount = elements.filter(el => el && !el.source).length
    if (incomingNodeCount === lastSyncNodeCount) return
    isSyncing = false
  }
  nodes.value = filterNodes(elements)
  edges.value = filterEdges(elements).map(edge => ({
    ...edge,
    type: edge.class === 'loop-edge' || edge.data?.edgeType === 'iterate' ? 'smoothstep' : 'default'
  }))

  if (!hasInitialLayout && nodes.value.length > 0) {
    hasInitialLayout = true
    const hasValidPositions = nodes.value.some(node => {
      const x = node.position?.x
      const y = node.position?.y
      return (x !== undefined && x !== 0) || (y !== undefined && y !== 0)
    })

    if (!hasValidPositions) {
      setTimeout(async () => {
        nodes.value = await autoLayout(nodes.value, edges.value)
        syncToParent()
        nextTick(() => { updateNodeInternals(nodes.value.map(n => n.id)) })
      }, 100)
    } else {
      nextTick(() => { updateNodeInternals(nodes.value.map(n => n.id)) })
    }
  }
}, { immediate: true })

// === Lifecycle ===
onMounted(() => {
  document.addEventListener('keydown', onKeyDown, true)
  restoreViewport(props.savedViewport)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeyDown, true)
  cleanupViewportTimer()
  cleanupArrowKeyTimer()
})

// Expose methods for parent component
defineExpose({
  autoLayout: handleAutoLayout
})
</script>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';
@import '@vue-flow/minimap/dist/style.css';
@import '../styles/vueflow-overrides.css';
@import '../assets/styles/canvas-minimap.css';
</style>

<style scoped>
.workflow-canvas-container {
  position: relative;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(1200px 600px at 50% 20%, rgba(30, 41, 59, 0.75), rgba(2, 6, 23, 0.95)),
    radial-gradient(600px 300px at 70% 80%, rgba(15, 23, 42, 0.6), transparent 60%);
  overflow: hidden;
}

.workflow-canvas-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.2), rgba(2, 6, 23, 0.6)),
    radial-gradient(circle at 10% 10%, rgba(99, 102, 241, 0.08), transparent 40%),
    radial-gradient(circle at 85% 20%, rgba(56, 189, 248, 0.08), transparent 45%);
  pointer-events: none;
  z-index: 0;
}

.workflow-canvas-container::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.04) 1px, transparent 1px);
  background-size: 120px 120px;
  opacity: 0.35;
  pointer-events: none;
  z-index: 0;
}

.workflow-canvas {
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 1;
}

/* Debug mode styles */
.workflow-canvas-container.debug-mode {
  cursor: crosshair;
}
</style>
