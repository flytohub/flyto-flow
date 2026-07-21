<template>
  <div class="loop-node" :class="nodeClasses">
    <!-- Delete button -->
    <button @click.stop="$emit('delete-node', { nodeId: id })" aria-label="Delete node" class="delete-btn">
      <X :size="14" />
    </button>

    <!-- Square shape container -->
    <div class="square-shape">
      <div class="shape-content">
        <component :is="icon" :size="20" class="node-icon" />
        <div class="node-label">{{ label }}</div>
      </div>
    </div>

    <!-- IN: Left -->
    <Handle
      id="in"
      type="target"
      :position="Position.Left"
      class="handle handle-in"
      :class="{ 'handle-hidden': isFirst }"
    />

    <!-- DONE_OUT: Right (continues after loop) -->
    <Handle
      id="done_out"
      type="source"
      :position="Position.Right"
      class="handle handle-done"
      title="Done"
    />

    <!-- Add button for done_out (right side) - hidden when already connected -->
    <button
      v-if="showAddButton && !hasDoneEdge"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: 'done_out' })"
      class="add-btn add-btn-right"
      title="After loop"
    >
      <Plus :size="14" />
    </button>

    <!-- Sub-port area (below card, AI Agent style) -->
    <div class="sub-ports">
      <div class="sub-port sub-port-body">
        <button
          v-if="showAddButton && !hasBodyEdge"
          @click.stop="$emit('add-node', { nodeId: id, sourceHandle: 'body_out' })"
          class="add-btn-sub"
          title="Add loop body"
        >
          <Repeat :size="14" />
        </button>
        <Handle
          id="body_out"
          type="source"
          :position="Position.Bottom"
          class="handle handle-sub handle-body"
          title="Body"
        />
        <div class="sub-port-label">Body</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Plus, X, Repeat } from 'lucide-vue-next'

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
  isFirst: Boolean,
  showAddButton: Boolean,
  hasCheckpoint: Boolean,
  icon: [Object, Function],
  label: { type: String, default: 'Loop' },
  disabled: { type: Boolean, default: false },
  edges: { type: Array, default: () => [] }
})

defineEmits(['add-node', 'delete-node'])

const hasBodyEdge = computed(() =>
  props.edges.some(e => e.source === props.id && e.sourceHandle === 'body_out')
)

const hasDoneEdge = computed(() =>
  props.edges.some(e => e.source === props.id && e.sourceHandle === 'done_out')
)

const nodeClasses = computed(() => ({
  'selected': props.selected,
  'dimmed': props.data?.dimmed,
  'has-checkpoint': props.hasCheckpoint,
  'node-disabled': props.disabled
}))
</script>

<style scoped>
.loop-node {
  position: relative;
  width: var(--node-loop-width, 76px);
  height: var(--node-loop-height, 76px);
  transition: transform 0.2s ease;
}


/* Square shape */
.square-shape {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #3B82F6;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.25);
  transition: all 0.2s ease;
}

.loop-node:hover .square-shape {
  border-color: #60A5FA;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.loop-node.selected .square-shape {
  border-color: transparent;
}

.loop-node.selected::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 14px;
  padding: 2px;
  background: linear-gradient(90deg, #3B82F6, #60A5FA, #3B82F6);
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

/* Content */
.shape-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.node-icon {
  color: #3B82F6;
}

.node-label {
  font-size: 10px;
  font-weight: 600;
  color: #f1f5f9;
  text-align: center;
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

/* IN: Left gray */
.handle-in {
  left: -5px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  background: #6B7280 !important;
}

/* DONE_OUT: Right green */
.handle-done {
  right: -5px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  background: #10B981 !important;
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

.loop-node:hover .delete-btn { opacity: 1; }
.delete-btn:hover { transform: scale(1.2); background: #DC2626; }

/* Add button (right side for done_out) */
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

.loop-node:hover .add-btn { opacity: 1; }
.add-btn-right:hover { transform: translateY(-50%) scale(1.15); }

.add-btn-right {
  right: -16px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
}

/* Bottom Sub-port area (AI Agent style) */
.sub-ports {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: 100%;
  margin-top: 8px;
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 0 12px;
}

.sub-port {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.sub-port-label {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #64748B;
  transition: color 0.3s ease;
}

/* Sub-port handle */
.handle-sub {
  position: relative !important;
  left: auto !important;
  top: auto !important;
  transform: none !important;
  width: 8px !important;
  height: 8px !important;
  margin-top: 2px;
  transition: all 0.3s ease;
}

.handle-body {
  background: #3B82F6 !important;
  border-color: #1E40AF !important;
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}

/* Sub-port add button (dashed circle) */
.add-btn-sub {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  border: 2px dashed #374151;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748B;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.add-btn-sub:hover {
  border-style: solid;
  transform: translateY(-2px);
}

.sub-port-body .add-btn-sub:hover {
  border-color: #3B82F6;
  color: #3B82F6;
  background: rgba(59, 130, 246, 0.1);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
}

.sub-port-body:hover .sub-port-label { color: #3B82F6; }


/* States */
.loop-node.dimmed { opacity: 0.4; pointer-events: none; }

/* Checkpoint - red ripple effect */
.loop-node.has-checkpoint .square-shape {
  border-color: #EF4444;
}

.loop-node.has-checkpoint::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 16px;
  border: 2px solid #EF4444;
  animation: ripple-ring 2.5s ease-out infinite;
  pointer-events: none;
}

.loop-node.has-checkpoint:hover .square-shape {
  border-color: #3B82F6;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.loop-node.has-checkpoint:hover::after {
  animation: none;
  opacity: 0;
}

/* ========== Disabled State ========== */
.loop-node.node-disabled {
  cursor: not-allowed;
}

.loop-node.node-disabled .handle {
  opacity: 0.4;
}

.loop-node.node-disabled .add-btn,
.loop-node.node-disabled .add-btn-sub {
  display: none;
}

.loop-node.node-disabled .square-shape {
  opacity: 0.5;
  filter: grayscale(40%);
}

@keyframes ripple-ring {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.3); opacity: 0; }
}
</style>
