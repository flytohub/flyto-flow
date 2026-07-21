<template>
  <div class="default-node" :class="nodeClasses">
    <!-- Delete button -->
    <button
      @click.stop="$emit('delete-node', { nodeId: id })"
      aria-label="Delete node"
      class="delete-btn"
      :disabled="isLockedByOther"
    >
      <X :size="14" />
    </button>

    <!-- Retry button (shown on error state) -->
    <button
      v-if="executionState === 'error'"
      @click.stop="$emit('retry-node', { nodeId: id })"
      class="retry-btn"
      title="Retry from this node"
    >
      <RotateCcw :size="14" />
    </button>

    <!-- Replace button (switch to different module) -->
    <button
      @click.stop="$emit('replace-node', { nodeId: id, moduleId: data?.module })"
      class="replace-btn"
      title="Replace with another module"
      :disabled="isLockedByOther"
    >
      <RefreshCw :size="14" />
    </button>

    <!-- Edit template button (only for template.invoke nodes) -->
    <button
      v-if="isTemplateNode && templateIdFromModule"
      @click.stop="$emit('edit-template', { templateId: templateIdFromModule })"
      class="edit-template-btn"
      title="Edit template"
    >
      <Pencil :size="14" />
    </button>

    <!-- Lock badge (collaboration) -->
    <NodeLockBadge
      v-if="showLockBadge"
      :node-id="id"
      class="lock-badge"
    />

    <!-- Collaboration selection ring (another user is viewing this node) -->
    <div
      v-if="selectedByOther"
      class="collab-selection-ring"
      :style="{ '--ring-color': selectedByOther.color }"
      :title="`${selectedByOther.displayName} is viewing this node`"
    />

    <!-- Node card -->
    <NodeCardContent
      :execution-state="executionState"
      :execution-duration="formattedDuration"
      :gradient="gradient"
      :icon="icon"
      :label="label"
      :subtitle="subtitle"
      :is-container="isContainer"
      :container-node-count="containerNodeCount"
      :status="status"
      :status-icon="statusIcon"
      :is-flow-control="isFlowControl"
      :node-output="nodeOutput"
      :node-input="nodeInput"
      :node-error="nodeError"
      :node-display-outputs="nodeDisplayOutputs"
      :is-pinned="isPinned"
      :validation="validation"
      :compact="compact"
      :disabled="disabled"
      :description="data?.description"
      :style="{ '--node-accent-color': categoryColor }"
      @edit-container="$emit('edit-container', $event)"
    />

    <!-- Handles -->
    <Handle
      id="target"
      type="target"
      :position="Position.Left"
      class="handle handle-target"
      :class="{ 'handle-hidden': isFirst }"
      :style="{ top: '50%', left: '-6px', transform: 'translateY(-50%)' }"
    />
    <Handle
      id="output"
      type="source"
      :position="Position.Right"
      class="handle handle-source"
      :style="{ top: '50%', right: '-6px', transform: 'translateY(-50%)' }"
    />

    <!-- Error output handle: bottom of node, flows downward on error -->
    <Handle
      v-if="showErrorHandle"
      id="source-error"
      type="source"
      :position="Position.Bottom"
      class="handle handle-error"
      title="Error output"
    />

    <!-- Top target handle (loop body or error entry) -->
    <Handle
      id="target-top"
      type="target"
      :position="Position.Top"
      class="handle handle-target-top"
      :class="{ 'handle-hidden': !hasLoop, 'handle-target-top-error': hasLoop === 'error' }"
    />

    <!-- Add button -->
    <button
      v-if="showAddButton"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: null })"
      aria-label="Add node"
      class="add-btn"
      :style="{ background: addBtnGradient }"
    >
      <Plus :size="16" />
    </button>

    <!-- Error add button (bottom, for error handle) -->
    <button
      v-if="showErrorHandle"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: 'source-error', edgeColor: '#EF4444' })"
      class="add-btn-error"
      title="Error"
    >
      <Plus :size="9" />
    </button>

    <!-- Category badge (hidden in compact mode) -->
    <div v-if="!compact" class="category-badge" :style="{ background: categoryColor }">
      {{ categoryLabel }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Plus, X, RotateCcw, RefreshCw, Pencil } from 'lucide-vue-next'
import NodeCardContent from '../NodeCardContent.vue'
import NodeLockBadge from '@/components/collaboration/NodeLockBadge.vue'
import { useCollaborationStore } from '@/stores/collaborationStore'
import { useNodeOutputStore } from '@/stores/execution/nodeOutputStore'

const collaborationStore = useCollaborationStore()
const nodeOutputStore = useNodeOutputStore()

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
  isFirst: Boolean,
  hasForwardEdge: Boolean,
  hasLoop: [Boolean, String],  // 'loop' | 'error' | false
  // Node config
  executionState: String,
  executionDuration: String,
  gradient: String,
  icon: [Object, Function],
  label: String,
  subtitle: String,
  isContainer: Boolean,
  containerNodeCount: Number,
  status: String,
  statusIcon: Object,
  isFlowControl: Boolean,
  nodeOutput: [Object, Array, String, Number, Boolean],
  isPinned: Boolean,
  validation: { type: Object, default: null },
  showAddButton: Boolean,
  // Style
  categoryColor: String,
  categoryLabel: String,
  addBtnGradient: String,
  hasCheckpoint: Boolean,
  showErrorHandle: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false }
})

defineEmits(['add-node', 'delete-node', 'edit-container', 'retry-node', 'replace-node', 'edit-template'])

// Template node detection
const isTemplateNode = computed(() => {
  const moduleId = props.data?.module || ''
  return typeof moduleId === 'string' && moduleId.startsWith('template.invoke:')
})

const templateIdFromModule = computed(() => {
  const moduleId = props.data?.module || ''
  if (!moduleId.startsWith('template.invoke:')) return null
  return moduleId.split('template.invoke:')[1] || null
})

// Collaboration lock state
const showLockBadge = computed(() => {
  if (!collaborationStore.isConnected) return false
  return !!collaborationStore.nodeLocks[props.id]
})

const isLockedByOther = computed(() => {
  if (!collaborationStore.isConnected) return false
  return collaborationStore.isNodeLockedByOther(props.id)
})

// Get node input, error, and display outputs from store
const nodeInput = computed(() => nodeOutputStore.getNodeInputs(props.id))
const nodeError = computed(() => nodeOutputStore.getNodeError(props.id))
const nodeDisplayOutputs = computed(() => nodeOutputStore.getNodeDisplayOutputs(props.id))

// Get execution duration from store and format it
const formattedDuration = computed(() => {
  const durationMs = nodeOutputStore.getNodeDuration(props.id)
  if (durationMs === null || durationMs === undefined) return props.executionDuration
  if (durationMs < 1000) return `${durationMs}ms`
  if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`
  return `${(durationMs / 60000).toFixed(1)}m`
})

// Collaboration: check if another user has selected/editing this node
const selectedByOther = computed(() => {
  if (!collaborationStore.isConnected) return null
  return collaborationStore.participants.find(
    p => p.userId !== collaborationStore.currentParticipantId
      && (p.selectedNode === props.id || p.editingNode === props.id)
  ) || null
})

const nodeClasses = computed(() => ({
  'selected': props.selected,
  'dimmed': props.data?.dimmed,
  'highlighted': props.data?.highlighted,
  'flow-control': props.isFlowControl,
  'container-node': props.isContainer,
  'debug-selected': props.data?.debugSelected,
  'has-checkpoint': props.hasCheckpoint,
  'execution-running': props.executionState === 'running',
  'execution-completed': props.executionState === 'completed',
  'execution-pending': props.executionState === 'pending',
  'execution-error': props.executionState === 'error',
  'compact-mode': props.compact,
  'node-disabled': props.disabled,
  'node-locked': isLockedByOther.value
}))
</script>

<style scoped>
/* Node dimensions from backend SSOT via CSS variables */
.default-node {
  position: relative;
  width: var(--node-standard-width, 240px);
  height: var(--node-standard-height, 76px);
  transition: transform 0.2s ease;
}

.default-node:hover {
  transform: translateY(-2px);
}

.default-node:hover :deep(.node-card) {
  border-color: #8B5CF6;
  box-shadow:
    0 12px 32px rgba(139, 92, 246, 0.35),
    0 0 24px rgba(139, 92, 246, 0.2);
}

.default-node.selected :deep(.node-card) {
  border-color: transparent !important;
}

.default-node.selected::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 18px;
  padding: 2px;
  background: linear-gradient(90deg, #8B5CF6, #06B6D4, #EC4899, #8B5CF6);
  background-size: 300% 100%;
  animation: border-flow 3s linear infinite;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}

@keyframes border-flow {
  0% { background-position: 0% 50%; }
  100% { background-position: 300% 50%; }
}

/* Handles */
.handle {
  width: 12px !important;
  height: 12px !important;
  border: 2px solid rgba(148, 163, 184, 0.65) !important;
  background: #0f172a !important;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.25);
  transition: all 0.2s ease;
  top: 50% !important;
  transform: translateY(-50%) !important;
}

.handle-target {
  left: -6px !important;
}

.handle-hidden {
  opacity: 0 !important;
  pointer-events: none !important;
}

.handle-source {
  right: -6px !important;
}

.default-node:hover .handle {
  border-color: #8B5CF6;
}

/* Top target handle (loop body entry = blue, error entry = red) */
.handle-target-top {
  top: -5px !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  background: #3B82F6 !important;
  border-color: #1E40AF !important;
  width: 10px !important;
  height: 10px !important;
}

.handle-target-top-error {
  background: #EF4444 !important;
  border-color: #991B1B !important;
}

/* Error output handle (bottom center) — must override .handle base top/transform */
.handle-error {
  top: auto !important;
  bottom: -6px !important;
  left: 50% !important;
  right: auto !important;
  transform: translateX(-50%) !important;
  background: #EF4444 !important;
  border-color: #374151 !important;
}

.default-node:hover .handle-error {
  transform: translateX(-50%) !important;
}

/* Delete button */
.delete-btn {
  position: absolute;
  top: -8px;
  left: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #EF4444;
  border: 2px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 20;
  color: white;
}

.default-node:hover .delete-btn { opacity: 1; }
.delete-btn:hover { transform: scale(1.2); background: #DC2626; }

/* Retry button */
.retry-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8B5CF6, #6366F1);
  border: 2px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 20;
  color: white;
}

.default-node:hover .retry-btn { opacity: 1; }
.retry-btn:hover { transform: scale(1.15); background: linear-gradient(135deg, #A78BFA, #818CF8); }

/* Replace button - next to delete button */
.replace-btn {
  position: absolute;
  top: -8px;
  left: 20px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #06B6D4, #0891B2);
  border: 2px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 20;
  color: white;
}

.default-node:hover .replace-btn { opacity: 1; }
.replace-btn:hover { transform: scale(1.15); background: linear-gradient(135deg, #22D3EE, #06B6D4); }

/* Edit template button - bottom left */
.edit-template-btn {
  position: absolute;
  bottom: -8px;
  left: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8B5CF6, #A855F7);
  border: 2px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 20;
  color: white;
}

.default-node:hover .edit-template-btn { opacity: 1; }
.edit-template-btn:hover { transform: scale(1.15); background: linear-gradient(135deg, #A78BFA, #C084FC); }

/* Add button */
.add-btn {
  position: absolute;
  right: -20px;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 10;
  color: white;
}

.default-node:hover .add-btn { opacity: 1; }
.add-btn:hover { transform: translateY(-50%) scale(1.15); }

/* Error add button (centered below error handle) */
.add-btn-error {
  position: absolute;
  left: 50%;
  bottom: -24px;
  transform: translateX(-50%);
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #EF4444;
  border: 1.5px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 10;
  color: white;
  font-size: 10px;
}

.default-node:hover .add-btn-error { opacity: 0.8; }
.add-btn-error:hover { opacity: 1 !important; transform: translateX(-50%) scale(1.15); }

/* Category badge */
.category-badge {
  position: absolute;
  top: -8px;
  right: 12px;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  color: white;
}

/* States */
.default-node.dimmed { opacity: 0.4; pointer-events: none; }
.default-node.flow-control :deep(.node-card) { border-style: dashed; }
.default-node.execution-running :deep(.node-card) {
  border-color: #8B5CF6;
  animation: running-pulse 1.5s ease-in-out infinite;
}
.default-node.execution-completed :deep(.node-card) {
  border-color: #10B981;
}
.default-node.execution-error :deep(.node-card) {
  border-color: #EF4444;
}

/* Checkpoint - 最高優先級，覆蓋所有其他邊框效果 */
.default-node.has-checkpoint :deep(.node-card) {
  border-color: #EF4444 !important;
  box-shadow: none !important;
}

/* Checkpoint 時隱藏 selected 的漸變邊框 */
.default-node.has-checkpoint.selected::before {
  display: none !important;
}

/* Checkpoint 時 hover 也保持紅色 */
.default-node.has-checkpoint:hover :deep(.node-card) {
  border-color: #EF4444 !important;
  box-shadow: none !important;
}

/* Checkpoint ripple - 在 wrapper 層級 */
.default-node.has-checkpoint::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 18px;
  border: 2px solid #EF4444;
  animation: ripple-ring 2.5s ease-out infinite;
  pointer-events: none;
  z-index: 5;
}

@keyframes ripple-ring {
  0% {
    transform: scale(1);
    opacity: 0.6;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

@keyframes running-pulse {
  0%, 100% { box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3); }
  50% { box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.4); }
}

/* ========== Compact Mode ========== */
.default-node.compact-mode {
  width: var(--node-compact-width, 64px);
  height: var(--node-compact-height, 64px);
}

.default-node.compact-mode:hover {
  transform: scale(1.05);
}

.default-node.compact-mode .delete-btn {
  top: -6px;
  left: -6px;
  width: 20px;
  height: 20px;
}

.default-node.compact-mode .add-btn {
  right: -16px;
  width: 28px;
  height: 28px;
}

.default-node.compact-mode:hover .add-btn {
  opacity: 1;
}

.default-node.compact-mode .handle {
  width: 10px !important;
  height: 10px !important;
}

.default-node.compact-mode .handle-target {
  left: -5px !important;
}

.default-node.compact-mode .handle-source {
  right: -5px !important;
}

.default-node.compact-mode.selected::before {
  border-radius: 16px;
}

/* ========== Disabled State ========== */
.default-node.node-disabled {
  cursor: not-allowed;
}

.default-node.node-disabled:hover {
  transform: none;
}

.default-node.node-disabled:hover :deep(.node-card) {
  border-color: #F97316;
  box-shadow: 0 0 12px rgba(249, 115, 22, 0.3);
}

.default-node.node-disabled .handle {
  opacity: 0.4;
}

.default-node.node-disabled .add-btn {
  display: none;
}

.default-node.node-disabled .category-badge {
  filter: grayscale(70%);
  opacity: 0.5;
}

/* ========== Lock Badge Position ========== */
.lock-badge {
  position: absolute;
  top: -10px;
  right: 40px;
  z-index: 15;
}

/* ========== Locked by Other State (behavior only - border in hierarchy) ========== */
.default-node.node-locked {
  cursor: not-allowed;
}

.default-node.node-locked:hover {
  transform: none;
}

.default-node.node-locked:hover :deep(.node-card) {
  /* Keep amber border on hover - don't override to purple */
  border-color: #f59e0b !important;
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.3);
}

.default-node.node-locked .delete-btn {
  display: none;
}

.default-node.node-locked .add-btn {
  opacity: 0.4;
  pointer-events: none;
}

.default-node.node-locked .handle {
  opacity: 0.5;
  pointer-events: none;
}

/* ========== Collaboration Selection Ring ========== */
.collab-selection-ring {
  position: absolute;
  inset: -4px;
  border: 2px solid var(--ring-color);
  border-radius: 18px;
  pointer-events: none;
  z-index: 1;
  animation: collab-pulse 2s ease-in-out infinite;
}

@keyframes collab-pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
</style>
