<template>
  <div class="branch-node" :class="nodeClasses">
    <!-- Delete button -->
    <button @click.stop="$emit('delete-node', { nodeId: id })" aria-label="Delete node" class="delete-btn">
      <X :size="14" />
    </button>

    <!-- Diamond shape container -->
    <div class="diamond-shape">
      <div class="diamond-inner">
        <div class="shape-content">
          <component :is="icon" :size="18" class="node-icon" />
          <div class="node-label">{{ label }}</div>
          <div class="path-indicators">
            <span class="path-dot true-dot"></span>
            <span class="path-dot false-dot"></span>
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

    <!-- TRUE: Right (green) -->
    <Handle
      id="source-true"
      type="source"
      :position="Position.Right"
      class="handle handle-right"
    />

    <!-- FALSE: Bottom (red) -->
    <Handle
      id="source-false"
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

    <!-- Add button for True (right) -->
    <button
      v-if="showAddButton"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: 'source-true', edgeColor: '#10B981' })"
      class="add-btn add-btn-right"
      title="True"
    >
      <Plus :size="14" />
    </button>

    <!-- Add button for False (bottom) -->
    <button
      v-if="showAddButton"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: 'source-false', edgeColor: '#EF4444' })"
      class="add-btn add-btn-bottom"
      title="False"
    >
      <Plus :size="14" />
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Plus, X } from 'lucide-vue-next'

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
  isFirst: Boolean,
  showAddButton: Boolean,
  hasLoop: [Boolean, String],
  hasCheckpoint: Boolean,
  label: { type: String, default: 'If/Else' },
  icon: [Object, Function],
  disabled: { type: Boolean, default: false }
})

defineEmits(['add-node', 'delete-node'])

const nodeClasses = computed(() => ({
  'selected': props.selected,
  'dimmed': props.data?.dimmed,
  'has-checkpoint': props.hasCheckpoint,
  'node-disabled': props.disabled
}))
</script>

<style scoped>
.branch-node {
  position: relative;
  width: var(--node-branch-width, 76px);
  height: var(--node-branch-height, 76px);
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
  border: 2px solid #8B5CF6;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.25);
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

.branch-node:hover .diamond-shape {
  border-color: #A78BFA;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
}

.branch-node.selected .diamond-shape {
  border-color: transparent;
}

.branch-node.selected::before {
  content: '';
  position: absolute;
  width: calc(var(--node-diamond-inner, 54px) + 4px);
  height: calc(var(--node-diamond-inner, 54px) + 4px);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(45deg);
  border-radius: 10px;
  background: linear-gradient(90deg, #8B5CF6, #A78BFA, #8B5CF6);
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
  color: #8B5CF6;
}

.node-label {
  font-size: 9px;
  font-weight: 600;
  color: #f1f5f9;
  text-align: center;
}

.path-indicators {
  display: flex;
  gap: 4px;
}

.path-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.true-dot {
  background: #10B981;
}

.false-dot {
  background: #EF4444;
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

/* Right - True (green) */
.handle-right {
  right: -5px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  background: #10B981 !important;
}

/* Bottom - False (red) */
.handle-bottom {
  left: 50% !important;
  bottom: -5px !important;
  top: auto !important;
  transform: translateX(-50%) !important;
  background: #EF4444 !important;
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

.branch-node:hover .delete-btn { opacity: 1; }
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

.branch-node:hover .add-btn { opacity: 1; }
.add-btn-right:hover { transform: translateY(-50%) scale(1.15); }
.add-btn-bottom:hover { transform: translateX(-50%) scale(1.15); }

.add-btn-right {
  right: -16px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
}

.add-btn-bottom {
  left: 50%;
  bottom: -16px;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
}


/* States */
.branch-node.dimmed { opacity: 0.4; pointer-events: none; }

/* Checkpoint - red ripple effect */
.branch-node.has-checkpoint .diamond-shape {
  border-color: #EF4444;
}

.branch-node.has-checkpoint::after {
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

.branch-node.has-checkpoint:hover .diamond-shape {
  border-color: #10B981;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
}

.branch-node.has-checkpoint:hover::after {
  animation: none;
  opacity: 0;
}

/* ========== Disabled State ========== */
.branch-node.node-disabled {
  cursor: not-allowed;
}

.branch-node.node-disabled .handle {
  opacity: 0.4;
}

.branch-node.node-disabled .add-btn {
  display: none;
}

.branch-node.node-disabled .diamond-shape {
  opacity: 0.5;
  filter: grayscale(40%);
}

@keyframes ripple-ring {
  0% { transform: translate(-50%, -50%) rotate(45deg) scale(1); opacity: 0.6; }
  100% { transform: translate(-50%, -50%) rotate(45deg) scale(1.3); opacity: 0; }
}
</style>
