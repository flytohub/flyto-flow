<template>
  <div class="node-card" :class="[cardClasses, executionStateClass, { 'node-card--compact': compact, 'node-card--disabled': disabled }]" :title="compact ? label : undefined">
    <!-- Execution badges, overlays, and disabled state -->
    <NodeExecutionBadges
      :execution-state="executionState"
      :execution-duration="executionDuration"
      :output-summary="outputSummary"
      :is-pinned="isPinned"
      :validation="validation"
      :compact="compact"
      :disabled="disabled"
      @show-details="showOutputDialog = true"
    />

    <!-- Icon container with category color -->
    <NodeCardIcon
      :icon="icon"
      :gradient="gradient"
      :label="label"
      :compact="compact"
    />

    <!-- Node content (hidden in compact mode) -->
    <div v-if="!compact" class="node-content">
      <div class="node-label">{{ label }}</div>
      <div class="node-subtitle">{{ subtitle }}</div>
      <!-- Node description (if provided) -->
      <div v-if="description" class="node-note" :title="description">
        <MessageSquare :size="10" class="note-icon" />
        <span class="note-text">{{ description }}</span>
      </div>
    </div>

    <!-- Container indicator - click to edit subflow (hidden in compact mode) -->
    <button
      v-if="isContainer && !compact"
      @click.stop="$emit('edit-container')"
      class="container-edit-indicator"
      :title="$t('container.editSubflow')"
    >
      <Layers :size="14" />
      <span class="container-count" v-if="containerNodeCount > 0">{{ containerNodeCount }}</span>
    </button>

    <!-- Container badge for compact mode -->
    <div v-if="isContainer && compact" class="container-compact-badge" :title="$t('container.editSubflow')">
      <Layers :size="10" />
    </div>

    <!-- Status indicator (hidden in compact mode) -->
    <div v-if="status && !isContainer && !compact" class="node-status" :class="`status-${status}`">
      <component :is="statusIcon" :size="12" aria-hidden="true" />
    </div>

    <!-- Execution Detail Dialog -->
    <ExecutionDetailDialog
      :show="showOutputDialog"
      :label="label"
      :duration="executionDuration"
      :node-output="nodeOutput"
      :node-input="nodeInput"
      :node-error="nodeError"
      :display-outputs="nodeDisplayOutputs"
      @close="showOutputDialog = false"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Layers, MessageSquare } from 'lucide-vue-next'
import NodeExecutionBadges from './nodes/NodeExecutionBadges.vue'
import NodeCardIcon from './nodes/NodeCardIcon.vue'
import ExecutionDetailDialog from './nodes/ExecutionDetailDialog.vue'

const props = defineProps({
  executionState: { type: String, default: null },
  executionDuration: { type: String, default: null },
  gradient: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  label: { type: String, required: true },
  subtitle: { type: String, default: '' },
  isContainer: { type: Boolean, default: false },
  containerNodeCount: { type: Number, default: 0 },
  status: { type: String, default: null },
  statusIcon: { type: [Object, Function], default: null },
  isFlowControl: { type: Boolean, default: false },
  cardClasses: { type: Object, default: () => ({}) },
  nodeOutput: { type: [Object, Array, String, Number, Boolean], default: null },
  nodeInput: { type: [Object, Array, String, Number, Boolean], default: null },
  nodeError: { type: [Object, String], default: null },
  nodeDisplayOutputs: { type: Array, default: () => [] },
  isPinned: { type: Boolean, default: false },
  validation: { type: Object, default: null },
  compact: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  description: { type: String, default: '' }
})

defineEmits(['edit-container'])

// Output dialog state
const showOutputDialog = ref(false)

// Generate a short summary of node output for the inline chip
const outputSummary = computed(() => {
  if (props.executionState !== 'completed') return null
  const output = props.nodeOutput
  if (output === null || output === undefined) return null

  if (Array.isArray(output)) {
    return `${output.length} items`
  }
  if (typeof output === 'object') {
    const keys = Object.keys(output)
    if (keys.length === 0) return null
    // Show status/message if available
    if (output.status) return String(output.status)
    if (output.message) return String(output.message).slice(0, 30)
    if (output.text) return String(output.text).slice(0, 30)
    if (output.result) return typeof output.result === 'string' ? output.result.slice(0, 30) : `${keys.length} keys`
    return `${keys.length} keys`
  }
  if (typeof output === 'string') {
    return output.length > 30 ? output.slice(0, 28) + '..' : output
  }
  return String(output)
})

const executionStateClass = computed(() => ({
  'state-running': props.executionState === 'running',
  'state-completed': props.executionState === 'completed',
  'state-pending': props.executionState === 'pending',
  'state-error': props.executionState === 'error'
}))
</script>

<style scoped>
.node-card {
  position: relative;
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  box-sizing: border-box;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(100, 116, 139, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(0, 0, 0, 0.1);
  transition: all 0.15s ease;
  backdrop-filter: blur(12px);
  overflow: hidden;
}

/* Left accent bar - category color indicator */
.node-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--node-accent-color, #6366F1);
  border-radius: 12px 0 0 12px;
  opacity: 0.8;
}

.node-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.node-label {
  font-weight: 600;
  font-size: 13px;
  color: #E5E7EB;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 1px;
  line-height: 1.3;
}

.node-subtitle {
  font-size: 10.5px;
  color: #6B7280;
  font-family: 'SF Mono', 'Cascadia Code', Monaco, monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

/* Node note/description */
.node-note {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-top: 6px;
  padding: 4px 6px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 6px;
  max-width: 100%;
}

.node-note .note-icon {
  flex-shrink: 0;
  color: #A78BFA;
  margin-top: 1px;
}

.node-note .note-text {
  font-size: 10px;
  color: #C4B5FD;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-word;
}

.node-status {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-running { background: #EFF6FF; color: #3B82F6; animation: pulse 1.5s infinite; }
.status-success { background: #ECFDF5; color: #10B981; }
.status-error { background: #FEF2F2; color: #EF4444; }
.status-pending { background: #F3F4F6; color: #6B7280; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* State-specific card styling */
.node-card.state-running {
  border-color: #8B5CF6;
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
}

.node-card.state-completed {
  border-color: #10B981;
}

.node-card.state-pending {
  border-color: #6B7280;
  opacity: 0.8;
}

.node-card.state-error {
  border-color: #EF4444;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
}

/* Container indicator */
.container-edit-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 8px;
  color: #A78BFA;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.container-edit-indicator:hover {
  background: rgba(139, 92, 246, 0.3);
  border-color: #8B5CF6;
  color: #C4B5FD;
  transform: scale(1.05);
}

.container-count {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: rgba(139, 92, 246, 0.4);
  border-radius: 9px;
  font-size: 10px;
  font-weight: 700;
}

/* ========== Compact Mode Styles ========== */
.node-card--compact {
  width: 64px;
  height: 64px;
  padding: 8px;
  gap: 0;
  justify-content: center;
  border-radius: 14px;
}

/* Container badge in compact mode */
.container-compact-badge {
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  border: 2px solid #1F2937;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  z-index: 15;
}

/* Compact mode hover effect */
.node-card--compact:hover {
  transform: scale(1.05);
}

/* ========== Disabled State ========== */
.node-card--disabled {
  opacity: 0.5;
  filter: grayscale(70%);
  pointer-events: auto;
}
</style>
