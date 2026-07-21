<template>
  <div class="ai-sub-node" :class="[nodeClasses, subTypeClass]">
    <!-- Glow ring effect -->
    <div class="glow-ring"></div>

    <!-- Delete button -->
    <button
      @click.stop="$emit('delete-node', { nodeId: id })"
      aria-label="Delete node"
      class="delete-btn"
    >
      <X :size="12" />
    </button>

    <!-- Top Handle - connects UP to AI Agent -->
    <Handle
      id="target"
      type="target"
      :position="Position.Top"
      class="handle handle-top"
    />

    <!-- Dashed card with icon -->
    <div class="sub-card">
      <div class="icon-wrapper">
        <component :is="subIcon" :size="18" />
      </div>
      <span class="sub-label">{{ displayLabel }}</span>
    </div>

    <!-- Pulse animation overlay -->
    <div class="pulse-overlay"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { X, Cpu, Brain, Wrench, Zap, Database, Bot } from 'lucide-vue-next'

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
  label: String,
  disabled: { type: Boolean, default: false },
  executionState: String
})

defineEmits(['delete-node'])

// Determine sub-node type from module ID
const subType = computed(() => {
  const moduleId = props.data?.module || ''
  const subNodeType = props.data?.subNodeType

  if (subNodeType === 'model' || moduleId.includes('model') || moduleId.startsWith('api.') || moduleId.startsWith('llm.')) {
    return 'model'
  }
  if (subNodeType === 'memory' || moduleId.includes('memory')) {
    return 'memory'
  }
  return 'tool'
})

const subTypeClass = computed(() => `type-${subType.value}`)

const subIcon = computed(() => {
  switch (subType.value) {
    case 'model': return Zap
    case 'memory': return Database
    default: return Wrench
  }
})

const displayLabel = computed(() => {
  if (props.label) return props.label
  switch (subType.value) {
    case 'model': return 'Model'
    case 'memory': return 'Memory'
    default: return 'Tool'
  }
})

const nodeClasses = computed(() => ({
  'selected': props.selected,
  'dimmed': props.data?.dimmed,
  'node-disabled': props.disabled,
  'execution-running': props.executionState === 'running',
  'execution-completed': props.executionState === 'completed',
  'execution-failed': props.executionState === 'failed'
}))
</script>

<style scoped>
.ai-sub-node {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Glow ring - pulsing background */
.glow-ring {
  position: absolute;
  inset: -4px;
  border-radius: 16px;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.ai-sub-node:hover .glow-ring {
  opacity: 1;
}

.type-model .glow-ring {
  background: radial-gradient(ellipse at center, rgba(16, 185, 129, 0.3) 0%, transparent 70%);
  animation: glow-pulse-green 2s ease-in-out infinite;
}

.type-memory .glow-ring {
  background: radial-gradient(ellipse at center, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
  animation: glow-pulse-purple 2s ease-in-out infinite;
}

.type-tool .glow-ring {
  background: radial-gradient(ellipse at center, rgba(245, 158, 11, 0.3) 0%, transparent 70%);
  animation: glow-pulse-orange 2s ease-in-out infinite;
}

/* Dashed card */
.sub-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: var(--node-ai-sub-width, 72px);
  min-height: var(--node-ai-sub-height, 56px);
  padding: 14px 18px;
  border: 2px dashed;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(8px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

/* Gradient border effect using pseudo-element */
.sub-card::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 16px;
  padding: 2px;
  background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-color-dark) 100%);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.ai-sub-node:hover .sub-card::before {
  opacity: 1;
}

/* Icon wrapper with glow */
.icon-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--icon-bg);
  box-shadow: 0 0 20px var(--icon-glow);
  transition: all 0.3s ease;
}

.ai-sub-node:hover .icon-wrapper {
  transform: scale(1.1);
  box-shadow: 0 0 30px var(--icon-glow);
}

/* Type-specific colors */
.type-model {
  --accent-color: #10B981;
  --accent-color-dark: #059669;
  --icon-bg: rgba(16, 185, 129, 0.2);
  --icon-glow: rgba(16, 185, 129, 0.4);
}

.type-model .sub-card {
  border-color: #10B981;
  color: #10B981;
}

.type-memory {
  --accent-color: #8B5CF6;
  --accent-color-dark: #7C3AED;
  --icon-bg: rgba(139, 92, 246, 0.2);
  --icon-glow: rgba(139, 92, 246, 0.4);
}

.type-memory .sub-card {
  border-color: #8B5CF6;
  color: #8B5CF6;
}

.type-tool {
  --accent-color: #F59E0B;
  --accent-color-dark: #D97706;
  --icon-bg: rgba(245, 158, 11, 0.2);
  --icon-glow: rgba(245, 158, 11, 0.4);
}

.type-tool .sub-card {
  border-color: #F59E0B;
  color: #F59E0B;
}

/* Hover states */
.ai-sub-node:hover .sub-card {
  border-style: solid;
  background: rgba(30, 41, 59, 0.95);
  transform: translateY(-2px);
}

.type-model:hover .sub-card {
  box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3), inset 0 1px 0 rgba(16, 185, 129, 0.2);
}

.type-memory:hover .sub-card {
  box-shadow: 0 8px 32px rgba(139, 92, 246, 0.3), inset 0 1px 0 rgba(139, 92, 246, 0.2);
}

.type-tool:hover .sub-card {
  box-shadow: 0 8px 32px rgba(245, 158, 11, 0.3), inset 0 1px 0 rgba(245, 158, 11, 0.2);
}

.sub-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.9;
}

/* Top handle with glow */
.handle-top {
  position: absolute !important;
  top: -6px !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  width: 10px !important;
  height: 10px !important;
  border: 2px solid #0F172A !important;
  border-radius: 50% !important;
  transition: all 0.3s ease;
}

.type-model .handle-top {
  background: #10B981 !important;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.type-memory .handle-top {
  background: #8B5CF6 !important;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.5);
}

.type-tool .handle-top {
  background: #F59E0B !important;
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
}

.ai-sub-node:hover .handle-top {
  transform: translateX(-50%) scale(1.2) !important;
}

/* Delete button */
.delete-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  border: 2px solid #0F172A;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  z-index: 20;
  color: white;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
}

.delete-btn:hover {
  transform: scale(1.1);
}

.ai-sub-node:hover .delete-btn { opacity: 1; }

/* Selected state */
.ai-sub-node.selected .sub-card {
  border-style: solid;
}

.ai-sub-node.selected.type-model .sub-card {
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.3), 0 8px 32px rgba(16, 185, 129, 0.3);
}

.ai-sub-node.selected.type-memory .sub-card {
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.3), 0 8px 32px rgba(139, 92, 246, 0.3);
}

.ai-sub-node.selected.type-tool .sub-card {
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.3), 0 8px 32px rgba(245, 158, 11, 0.3);
}

.ai-sub-node.dimmed { opacity: 0.4; }

/* ========== Disabled State ========== */
.ai-sub-node.node-disabled {
  cursor: not-allowed;
}

.ai-sub-node.node-disabled .sub-card {
  opacity: 0.5;
  filter: grayscale(40%);
}

.ai-sub-node.node-disabled:hover .sub-card {
  transform: none;
}

.ai-sub-node.node-disabled .handle {
  opacity: 0.4;
}

/* Pulse animation overlay */
.pulse-overlay {
  position: absolute;
  inset: 0;
  border-radius: 14px;
  pointer-events: none;
  opacity: 0;
}

.ai-sub-node.selected .pulse-overlay {
  animation: border-pulse 2s ease-in-out infinite;
}

/* Animations */
@keyframes glow-pulse-green {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

@keyframes glow-pulse-purple {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

@keyframes glow-pulse-orange {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

@keyframes border-pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--accent-color); }
  50% { box-shadow: 0 0 0 4px transparent; }
}

/* Execution state styles */
.ai-sub-node.execution-running .sub-card {
  border-style: solid;
  animation: sub-node-running 1.5s ease-in-out infinite;
}

.ai-sub-node.execution-completed .sub-card {
  border-color: #10B981;
  border-style: solid;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.3);
}

.ai-sub-node.execution-failed .sub-card {
  border-color: #EF4444;
  border-style: solid;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.3);
}

@keyframes sub-node-running {
  0%, 100% { border-color: var(--accent-color); box-shadow: 0 0 4px var(--accent-color); }
  50% { border-color: transparent; box-shadow: none; }
}
</style>
