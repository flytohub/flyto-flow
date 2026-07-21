<template>
  <div class="switch-node" :class="nodeClasses">
    <!-- Delete button -->
    <button @click.stop="$emit('delete-node', { nodeId: id })" aria-label="Delete node" class="delete-btn">
      <X :size="14" />
    </button>

    <!-- Diamond shape container -->
    <div class="diamond-shape">
      <div class="diamond-inner">
        <div class="shape-content">
          <component :is="icon" :size="18" class="node-icon" />
          <div class="node-label">{{ displayLabel }}</div>
          <div class="case-indicators">
            <span v-for="(c, i) in effectiveCases.slice(0, 3)" :key="c.id" class="case-dot" :style="{ background: c.color }"></span>
            <span v-if="effectiveCases.length > 3" class="more-cases">+{{ effectiveCases.length - 3 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- INPUT: Left -->
    <Handle
      id="target"
      type="target"
      :position="Position.Left"
      class="handle handle-left"
      :class="{ 'handle-hidden': isFirst }"
    />

    <!-- CASE outputs: Right (one handle per case) -->
    <Handle
      v-for="(c, i) in effectiveCases"
      :key="`handle-${c.id}`"
      :id="`source-case-${c.id}`"
      type="source"
      :position="Position.Right"
      class="handle handle-case"
      :style="caseHandleStyle(i)"
    />
    <!-- Fallback handle when no cases exist yet -->
    <Handle
      v-if="effectiveCases.length === 0"
      id="source-cases"
      type="source"
      :position="Position.Right"
      class="handle handle-right"
    />

    <!-- DEFAULT: Bottom -->
    <Handle
      id="source-default"
      type="source"
      :position="Position.Bottom"
      class="handle handle-bottom"
    />

    <!-- Top target handle (loop body entry) -->
    <Handle
      id="target-top"
      type="target"
      :position="Position.Top"
      class="handle handle-target-top"
      :class="{ 'handle-hidden': !hasLoop, 'handle-target-top-error': hasLoop === 'error' }"
    />

    <!-- Add button for cases (right) -->
    <button
      v-if="showAddButton"
      @click.stop="handleCaseAddClick"
      class="add-btn add-btn-right"
      :title="t('workflow.switch.cases')"
    >
      <Plus :size="14" />
    </button>

    <!-- Add button for default (bottom) -->
    <button
      v-if="showAddButton"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: 'source-default' })"
      class="add-btn add-btn-bottom"
      :title="t('workflow.switch.default')"
    >
      <Plus :size="14" />
    </button>

    <!-- Case selector is removed — "+" always creates a new case.
         To connect to an existing case, drag from the case handle directly. -->
  </div>
</template>

<script setup>
import { computed, watch, nextTick, watchEffect, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Handle, Position, useVueFlow } from '@vue-flow/core'
import { Plus, X } from 'lucide-vue-next'
import { CASE_COLORS } from '../../../config/nodeTypes/SwitchNode'

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
  isFirst: Boolean,
  showAddButton: Boolean,
  hasLoop: [Boolean, String],
  hasCheckpoint: Boolean,
  icon: [Object, Function],
  cases: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['add-node', 'delete-node'])

const { t } = useI18n()
const { updateNodeInternals } = useVueFlow()

// Effective cases: use prop (from dynamicOutputs/metadata) if available,
// otherwise fall back to data.params.cases directly.
// This ensures case handles ALWAYS exist regardless of metadata loading order.
const effectiveCases = computed(() => {
  if (props.cases.length > 0) return props.cases
  const rawCases = props.data?.params?.cases
  if (!rawCases || !Array.isArray(rawCases)) return []
  return rawCases.map((c, i) => ({
    id: c.id,
    color: CASE_COLORS[i % CASE_COLORS.length],
    label: c.label || c.value || `Case ${i + 1}`
  }))
})

// Dynamic handles require updateNodeInternals after DOM update,
// otherwise Vue Flow uses stale/fallback handle positions for edge routing.
watchEffect(() => {
  const len = effectiveCases.value.length
  if (len >= 0 && props.id) {
    nextTick(() => updateNodeInternals(props.id))
  }
})

// Also force update after mount (handles may not be registered yet during watchEffect)
onMounted(() => {
  if (props.id) {
    setTimeout(() => updateNodeInternals(props.id), 50)
  }
})

const nodeClasses = computed(() => ({
  'selected': props.selected,
  'dimmed': props.data?.dimmed,
  'has-checkpoint': props.hasCheckpoint,
  'node-disabled': props.disabled
}))

const displayLabel = computed(() => props.label || t('workflow.switch.label'))

// Position case handles vertically along the right side of the diamond
function caseHandleStyle(index) {
  const total = effectiveCases.value.length
  const color = effectiveCases.value[index]?.color || '#8B5CF6'
  if (total === 1) {
    return { background: color, borderColor: color }
  }
  // Spread handles vertically: center ± offset
  const spacing = Math.min(14, 36 / total)
  const offset = (index - (total - 1) / 2) * spacing
  return {
    top: `calc(50% + ${offset}px)`,
    transform: 'translateY(-50%)',
    background: color,
    borderColor: color
  }
}

// "+" opens module menu — reuse unconnected case first, or create new case after module selection
function handleCaseAddClick() {
  const cases = props.data?.params?.cases || []

  // Find first existing case that has no edge connected to it
  const unconnectedCase = cases.find(c => {
    const handleId = `source-case-${c.id}`
    return !props.edges.some(e => e.source === props.id && e.sourceHandle === handleId)
  })

  if (unconnectedCase) {
    // Reuse existing unconnected case (e.g. Case 1 that was never connected)
    const caseIndex = cases.indexOf(unconnectedCase)
    const color = CASE_COLORS[caseIndex % CASE_COLORS.length]
    emit('add-node', {
      nodeId: props.id,
      sourceHandle: `source-case-${unconnectedCase.id}`,
      caseId: unconnectedCase.id,
      caseColor: color
      // No pendingCase — case already exists in params
    })
    return
  }

  // All existing cases are connected — create a new one (deferred to module selection)
  const newIndex = cases.length + 1
  const newCase = {
    id: `case_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
    value: `case${newIndex}`,
    label: `Case ${newIndex}`,
    color: CASE_COLORS[cases.length % CASE_COLORS.length]
  }
  const newColor = CASE_COLORS[cases.length % CASE_COLORS.length]

  emit('add-node', {
    nodeId: props.id,
    sourceHandle: `source-case-${newCase.id}`,
    caseId: newCase.id,
    caseColor: newColor,
    pendingCase: newCase
  })
}
</script>

<style scoped>
.switch-node {
  position: relative;
  width: var(--node-switch-width, 76px);
  height: var(--node-switch-height, 76px);
  transition: transform 0.2s ease;
}


/* Diamond shape (rotated square): inner = outer / sqrt(2) ≈ 71% */
.diamond-shape {
  width: var(--node-diamond-inner, 54px);
  height: var(--node-diamond-inner, 54px);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #EC4899;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(236, 72, 153, 0.25);
  transition: all 0.2s ease;
  overflow: hidden;
}

.diamond-inner {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.switch-node:hover .diamond-shape {
  border-color: #F472B6;
  box-shadow: 0 8px 24px rgba(236, 72, 153, 0.4);
}

.switch-node.selected .diamond-shape {
  border-color: transparent;
}

.switch-node.selected::before {
  content: '';
  position: absolute;
  width: calc(var(--node-diamond-inner, 54px) + 4px);
  height: calc(var(--node-diamond-inner, 54px) + 4px);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  border-radius: 10px;
  background: linear-gradient(90deg, #EC4899, #F472B6, #EC4899);
  background-size: 300% 100%;
  animation: border-flow 3s linear infinite;
  z-index: -1;
}

@keyframes border-flow {
  0% { background-position: 0% 50%; }
  100% { background-position: 300% 50%; }
}

/* Content (counter-rotate to stay upright) */
.shape-content {
  transform: rotate(-45deg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.node-icon {
  color: #EC4899;
}

.node-label {
  font-size: 9px;
  font-weight: 600;
  color: #f1f5f9;
  text-align: center;
}

.case-indicators {
  display: flex;
  gap: 3px;
  align-items: center;
}

.case-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
}

.more-cases {
  font-size: 7px;
  color: #64748b;
}

/* Handles */
.handle {
  width: 10px !important;
  height: 10px !important;
  border: 2px solid #374151 !important;
  border-radius: 50% !important;
}

.handle-hidden {
  opacity: 0 !important;
  pointer-events: none !important;
}

/* Left - input */
.handle-left {
  left: -5px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  background: #6B7280 !important;
}

/* Right - cases (single fallback) */
.handle-right {
  right: -5px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  background: #8B5CF6 !important;
}

/* Right - per-case dynamic handles */
.handle-case {
  right: -5px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
}

/* Bottom - default */
.handle-bottom {
  left: 50% !important;
  bottom: -5px !important;
  top: auto !important;
  transform: translateX(-50%) !important;
  background: #6B7280 !important;
}

/* Top target handle (loop body entry) */
.handle-target-top {
  left: 50% !important;
  top: -5px !important;
  transform: translateX(-50%) !important;
  background: #3B82F6 !important;
  border-color: #1E40AF !important;
}

.handle-target-top-error {
  background: #EF4444 !important;
  border-color: #991B1B !important;
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

.switch-node:hover .delete-btn { opacity: 1; }
.delete-btn:hover { transform: scale(1.2); background: #DC2626; }

/* Add buttons */
.add-btn {
  position: absolute;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 10;
  color: white;
}

.switch-node:hover .add-btn { opacity: 1; }
.add-btn-right:hover { transform: translateY(-50%) scale(1.15); }
.add-btn-bottom:hover { transform: translateX(-50%) scale(1.15); }

.add-btn-right {
  right: -16px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
}

.add-btn-bottom {
  left: 50%;
  bottom: -16px;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);
}

/* States */
.switch-node.dimmed { opacity: 0.4; pointer-events: none; }

/* Checkpoint - red ripple effect */
.switch-node.has-checkpoint .diamond-shape {
  border-color: #EF4444;
}

.switch-node.has-checkpoint::after {
  content: '';
  position: absolute;
  width: calc(var(--node-diamond-inner, 54px) + 4px);
  height: calc(var(--node-diamond-inner, 54px) + 4px);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  border-radius: 10px;
  border: 2px solid #EF4444;
  animation: ripple-ring 2.5s ease-out infinite;
  pointer-events: none;
}

.switch-node.has-checkpoint:hover .diamond-shape {
  border-color: #EC4899;
  box-shadow: 0 8px 24px rgba(236, 72, 153, 0.4);
}

.switch-node.has-checkpoint:hover::after {
  animation: none;
  opacity: 0;
}

/* ========== Disabled State ========== */
.switch-node.node-disabled {
  cursor: not-allowed;
}

.switch-node.node-disabled .handle {
  opacity: 0.4;
}

.switch-node.node-disabled .add-btn {
  display: none;
}

.switch-node.node-disabled .diamond-shape {
  opacity: 0.5;
  filter: grayscale(40%);
}

@keyframes ripple-ring {
  0% { transform: translate(-50%, -50%) rotate(45deg) scale(1); opacity: 0.6; }
  100% { transform: translate(-50%, -50%) rotate(45deg) scale(1.3); opacity: 0; }
}
</style>
