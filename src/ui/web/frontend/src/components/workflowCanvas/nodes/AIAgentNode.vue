<template>
  <div class="ai-agent-node" :class="nodeClasses">
    <!-- Delete button -->
    <button
      @click.stop="$emit('delete-node', { nodeId: id })"
      aria-label="Delete node"
      class="delete-btn"
    >
      <X :size="14" />
    </button>

    <!-- Node card (identical to DefaultNode) -->
    <NodeCardContent
      :execution-state="executionState"
      :gradient="gradient || 'linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%)'"
      :icon="icon || Bot"
      :label="label || 'AI Agent'"
      :subtitle="modelSubtitle"
      :node-output="nodeOutput"
      :is-pinned="isPinned"
      :disabled="disabled"
      :validation="validation"
      :compact="compact"
    />

    <!-- Handles (identical to DefaultNode) -->
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

    <!-- Add button -->
    <button
      v-if="showAddButton"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: null })"
      aria-label="Add node"
      class="add-btn"
      :style="{ background: addBtnGradient || 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)' }"
    >
      <Plus :size="16" />
    </button>

    <!-- Category badge (same as DefaultNode, just AI content) -->
    <div v-if="!compact" class="category-badge" :style="{ background: categoryColor || 'linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)' }">
      <Sparkles :size="8" />
      <span>{{ categoryLabel || 'AI' }}</span>
    </div>

    <!-- ============ AI-ONLY: Agent activity (execution) ============ -->
    <div v-if="executionState === 'running' && agentActivity" class="agent-activity">
      <div class="activity-dots">
        <span /><span /><span />
      </div>
      <span class="activity-text">{{ activeToolLabel }}</span>
    </div>

    <!-- ============ AI-ONLY: Sub-node connection strip ============ -->
    <div class="sub-strip">
      <button
        type="button"
        @click.stop="emitResourceAdd('target-model', 'model', 'model')"
        class="sub-slot sub-slot-model"
        :class="{ 'sub-slot-disabled': modelSlotLocked, 'sub-slot-connected': modelSlotCount > 0 }"
        :disabled="modelSlotLocked"
        :aria-disabled="modelSlotLocked"
        title="Model"
      >
        <Handle id="target-model" type="target" :position="Position.Bottom" class="handle handle-sub" />
        <Zap :size="10" />
        <span class="sub-label">{{ modelSlotLabel }}</span>
      </button>

      <div class="sub-divider" />

      <button
        type="button"
        @click.stop="emitResourceAdd('target-memory', 'memory', 'memory')"
        class="sub-slot sub-slot-memory"
        :class="{ 'sub-slot-disabled': memorySlotLocked, 'sub-slot-connected': memorySlotCount > 0 }"
        :disabled="memorySlotLocked"
        :aria-disabled="memorySlotLocked"
        title="Memory"
      >
        <Handle id="target-memory" type="target" :position="Position.Bottom" class="handle handle-sub" />
        <Database :size="10" />
        <span class="sub-label">{{ memorySlotLabel }}</span>
      </button>

      <div class="sub-divider" />

      <button
        type="button"
        @click.stop="emitResourceAdd('target-tools', 'tools', 'tool')"
        class="sub-slot sub-slot-tools"
        title="Tools"
      >
        <Handle id="target-tools" type="target" :position="Position.Bottom" class="handle handle-sub" />
        <Wrench :size="10" />
        <span class="sub-label">{{ toolsSlotLabel }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Plus, X, Bot, Zap, Database, Wrench, Sparkles } from 'lucide-vue-next'
import NodeCardContent from '../NodeCardContent.vue'

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
  isFirst: Boolean,
  hasForwardEdge: Boolean,
  hasLoop: [Boolean, String],
  executionState: String,
  gradient: String,
  icon: [Object, Function],
  label: String,
  subtitle: String,
  status: String,
  nodeOutput: [Object, Array, String, Number, Boolean],
  isPinned: Boolean,
  showAddButton: Boolean,
  hasCheckpoint: Boolean,
  categoryColor: String,
  categoryLabel: String,
  addBtnGradient: String,
  validation: { type: Object, default: null },
  compact: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  agentActivity: { type: Object, default: null },
  resourceSlots: {
    type: Object,
    default: () => ({
      model: { count: 0, locked: false },
      memory: { count: 0, locked: false },
      tools: { count: 0, locked: false }
    })
  }
})

const emit = defineEmits(['add-node', 'delete-node'])

const modelSubtitle = computed(() => {
  const model = props.data?.params?.model || ''
  const provider = props.data?.params?.provider || ''
  if (model) return model
  if (provider) return provider
  return 'llm.agent'
})

const activeToolLabel = computed(() => {
  if (!props.agentActivity) return ''
  const tool = (props.agentActivity.tool || '').replace('--', '.')
  const iter = props.agentActivity.iteration || 0
  const max = props.agentActivity.maxIterations || '?'
  return tool ? `${tool} (${iter}/${max})` : `iter ${iter}/${max}`
})

const modelSlotCount = computed(() => props.resourceSlots?.model?.count || 0)
const memorySlotCount = computed(() => props.resourceSlots?.memory?.count || 0)
const toolsSlotCount = computed(() => props.resourceSlots?.tools?.count || 0)
const modelSlotLocked = computed(() => props.resourceSlots?.model?.locked === true)
const memorySlotLocked = computed(() => props.resourceSlots?.memory?.locked === true)
const modelSlotLabel = computed(() => modelSlotCount.value > 0 ? `Model ${modelSlotCount.value}` : 'Model')
const memorySlotLabel = computed(() => memorySlotCount.value > 0 ? `Memory ${memorySlotCount.value}` : 'Memory')
const toolsSlotLabel = computed(() => toolsSlotCount.value > 0 ? `Tools ${toolsSlotCount.value}` : 'Tools')

function emitResourceAdd(targetHandle, filter, subNodeType) {
  if ((targetHandle === 'target-model' && modelSlotLocked.value) ||
      (targetHandle === 'target-memory' && memorySlotLocked.value)) {
    return
  }
  emit('add-node', { nodeId: props.id, targetHandle, filter, subNodeType })
}

const nodeClasses = computed(() => ({
  'selected': props.selected,
  'dimmed': props.data?.dimmed,
  'highlighted': props.data?.highlighted,
  'has-checkpoint': props.hasCheckpoint,
  'execution-running': props.executionState === 'running',
  'execution-completed': props.executionState === 'completed',
  'execution-pending': props.executionState === 'pending',
  'execution-error': props.executionState === 'error',
  'node-disabled': props.disabled
}))
</script>

<style scoped>
/* ══════════════════════════════════════════════════════════
   Base layout, handles, buttons, states —
   COPIED from DefaultNode.vue, zero custom overrides.
   ══════════════════════════════════════════════════════════ */

.ai-agent-node {
  position: relative;
  width: var(--node-standard-width, 240px);
  height: var(--node-standard-height, 76px);
  transition: transform 0.2s ease;
}

.ai-agent-node:hover {
  transform: translateY(-2px);
}

.ai-agent-node:hover :deep(.node-card) {
  border-color: #8B5CF6;
  box-shadow:
    0 12px 32px rgba(139, 92, 246, 0.35),
    0 0 24px rgba(139, 92, 246, 0.2);
}

.ai-agent-node.selected :deep(.node-card) {
  border-color: transparent !important;
}

.ai-agent-node.selected::before {
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

.handle-target { left: -6px !important; }
.handle-source { right: -6px !important; }
.handle-hidden { opacity: 0 !important; pointer-events: none !important; }
.ai-agent-node:hover .handle { border-color: #8B5CF6 !important; }

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

.ai-agent-node:hover .delete-btn { opacity: 1; }
.delete-btn:hover { transform: scale(1.2); background: #DC2626; }

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

.ai-agent-node:hover .add-btn { opacity: 1; }
.add-btn:hover { transform: translateY(-50%) scale(1.15); }

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
  display: flex;
  align-items: center;
  gap: 3px;
}

/* States — identical to DefaultNode */
.ai-agent-node.dimmed { opacity: 0.4; pointer-events: none; }

.ai-agent-node.execution-running :deep(.node-card) {
  border-color: #8B5CF6;
  animation: running-pulse 1.5s ease-in-out infinite;
}

.ai-agent-node.execution-completed :deep(.node-card) {
  border-color: #10B981;
}

.ai-agent-node.execution-error :deep(.node-card) {
  border-color: #EF4444;
}

.ai-agent-node.has-checkpoint :deep(.node-card) {
  border-color: #EF4444 !important;
  box-shadow: none !important;
}

.ai-agent-node.has-checkpoint.selected::before {
  display: none !important;
}

.ai-agent-node.has-checkpoint:hover :deep(.node-card) {
  border-color: #EF4444 !important;
  box-shadow: none !important;
}

.ai-agent-node.has-checkpoint::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 18px;
  border: 2px solid #EF4444;
  animation: ripple-ring 2.5s ease-out infinite;
  pointer-events: none;
  z-index: 5;
}

.ai-agent-node.node-disabled { cursor: not-allowed; }
.ai-agent-node.node-disabled:hover { transform: none; }
.ai-agent-node.node-disabled:hover :deep(.node-card) {
  border-color: #F97316;
  box-shadow: 0 0 12px rgba(249, 115, 22, 0.3);
}
.ai-agent-node.node-disabled .handle { opacity: 0.4; }
.ai-agent-node.node-disabled .add-btn { display: none; }
.ai-agent-node.node-disabled .category-badge { filter: grayscale(70%); opacity: 0.5; }

@keyframes running-pulse {
  0%, 100% { box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3); }
  50% { box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.4); }
}

@keyframes ripple-ring {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.3); opacity: 0; }
}

/* ══════════════════════════════════════════════════════════
   AI-ONLY visual enhancements — base behavior unchanged.
   ══════════════════════════════════════════════════════════ */

/* Subtle ambient purple glow (always on, blends with hover naturally) */
.ai-agent-node :deep(.node-card) {
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.3),
    0 0 16px rgba(139, 92, 246, 0.12),
    inset 0 1px 0 rgba(139, 92, 246, 0.08);
}

/* Category badge shimmer */
.category-badge {
  overflow: hidden;
}

.category-badge::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: badge-shimmer 4s ease-in-out infinite;
}

@keyframes badge-shimmer {
  0%, 80% { left: -100%; }
  100% { left: 200%; }
}

/* ── Agent Activity Indicator (visible only during execution) ── */
.agent-activity {
  position: absolute;
  bottom: -26px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 12px;
  white-space: nowrap;
  z-index: 10;
  backdrop-filter: blur(8px);
}

.activity-dots {
  display: flex;
  gap: 3px;
}

.activity-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #A78BFA;
  animation: dot-bounce 1.4s ease-in-out infinite;
}

.activity-dots span:nth-child(2) { animation-delay: 0.2s; }
.activity-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}

.activity-text {
  font-size: 10px;
  color: #C4B5FD;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: 'SF Mono', Monaco, monospace;
}

/* ── Sub-Node Connection Strip (hover to reveal) ────────────── */
.sub-strip {
  position: absolute;
  left: 12px;
  right: 12px;
  top: 100%;
  margin-top: 4px;
  display: flex;
  align-items: center;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(100, 116, 139, 0.15);
  border-radius: 8px;
  padding: 2px;
  opacity: 0.4;
  transition: all 0.2s ease;
  backdrop-filter: blur(4px);
  z-index: 10;
}

.ai-agent-node:hover .sub-strip,
.sub-strip:hover {
  opacity: 1;
  background: rgba(15, 23, 42, 0.8);
  border-color: rgba(100, 116, 139, 0.3);
}

.sub-slot {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px 0;
  border-radius: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #64748B;
  transition: all 0.15s ease;
}

.sub-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.sub-divider {
  width: 1px;
  height: 14px;
  background: rgba(100, 116, 139, 0.2);
  flex-shrink: 0;
}

.sub-slot-model:hover { background: rgba(16, 185, 129, 0.12); color: #10B981; }
.sub-slot-memory:hover { background: rgba(139, 92, 246, 0.12); color: #A78BFA; }
.sub-slot-tools:hover { background: rgba(245, 158, 11, 0.12); color: #F59E0B; }

.sub-slot-disabled,
.sub-slot-disabled:hover {
  opacity: 0.55;
  cursor: not-allowed;
  background: transparent;
}

.sub-slot-connected:not(.sub-slot-disabled) {
  color: #CBD5E1;
}

.handle-sub {
  position: absolute !important;
  width: 6px !important;
  height: 6px !important;
  bottom: -5px !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  top: auto !important;
  border-width: 1.5px !important;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.sub-slot:hover .handle-sub { opacity: 1; }

.sub-slot-model .handle-sub { background: #10B981 !important; border-color: #065F46 !important; }
.sub-slot-memory .handle-sub { background: #8B5CF6 !important; border-color: #4C1D95 !important; }
.sub-slot-tools .handle-sub { background: #F59E0B !important; border-color: #92400E !important; }
</style>
