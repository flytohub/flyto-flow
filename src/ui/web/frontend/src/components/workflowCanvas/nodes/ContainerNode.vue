<template>
  <div
    class="container-node"
    :class="nodeClasses"
    @dblclick.stop="handleDoubleClick"
  >
    <!-- Delete button -->
    <button @click.stop="$emit('delete-node', { nodeId: id })" aria-label="Delete node" class="delete-btn">
      <X :size="14" />
    </button>

    <!-- Save as Template button -->
    <button
      @click.stop="$emit('save-as-template', { nodeId: id })"
      class="save-tpl-btn"
      title="Save as Template"
    >
      <BookTemplate :size="14" />
    </button>

    <!-- Collapse toggle button -->
    <button
      v-if="nodeCount > 0"
      @click.stop="toggleCollapse"
      class="collapse-btn"
      :title="isCollapsed ? 'Expand' : 'Collapse'"
    >
      <component :is="isCollapsed ? ChevronDown : ChevronUp" :size="12" />
    </button>

    <!-- Node count badge (shown when no minimap or collapsed) -->
    <div v-if="nodeCount > 0 && (isCollapsed || nodeCount > 5)" class="node-count-badge">
      {{ nodeCount }}
    </div>

    <!-- Container shape -->
    <div class="container-shape">
      <div class="shape-content">
        <!-- Minimap preview (non-collapsed, <= 5 nodes) -->
        <div v-if="!isCollapsed && childNodes.length > 0 && childNodes.length <= 5" class="minimap-preview">
          <div
            v-for="child in childNodes"
            :key="child.id"
            class="mini-node"
            :style="{ background: child.color }"
            :title="child.label"
          >
            <component v-if="child.icon && !child.isUrl" :is="child.icon" :size="10" />
            <img v-else-if="child.isUrl" :src="child.url" class="mini-icon-img" />
            <Box v-else :size="10" />
          </div>
        </div>
        <!-- Fallback icon when collapsed or many nodes -->
        <template v-if="isCollapsed || childNodes.length === 0 || childNodes.length > 5">
          <Layers :size="22" class="node-icon" />
          <div class="node-label">{{ label || 'Container' }}</div>
        </template>
      </div>

      <!-- Nested layers indicator -->
      <div class="layers-indicator">
        <div class="layer layer-1"></div>
        <div class="layer layer-2"></div>
      </div>
    </div>

    <!-- IN: Left -->
    <Handle
      id="target"
      type="target"
      :position="Position.Left"
      class="handle handle-in"
      :class="{ 'handle-hidden': isFirst }"
    />

    <!-- OUT: Right -->
    <Handle
      id="output"
      type="source"
      :position="Position.Right"
      class="handle handle-out"
    />

    <!-- Add button -->
    <button
      v-if="showAddButton"
      @click.stop="$emit('add-node', { nodeId: id, sourceHandle: 'output' })"
      aria-label="Add node"
      class="add-btn"
    >
      <Plus :size="14" />
    </button>

    <!-- Edit hint on hover -->
    <div class="edit-hint">
      <MousePointerClick :size="12" />
      <span>Double-click to edit</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import { Plus, X, Layers, MousePointerClick, ChevronDown, ChevronUp, BookTemplate, Box } from 'lucide-vue-next'
import { useNodeStyles } from '@/composables/useNodeStyles'

const { getNodeIcon, getCategoryColor, getNodeLabel, isCustomUrlIcon } = useNodeStyles()

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
  isFirst: Boolean,
  showAddButton: Boolean,
  hasCheckpoint: Boolean,
  icon: [Object, Function],
  label: { type: String, default: 'Container' },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['add-node', 'delete-node', 'edit-container', 'update:data', 'save-as-template'])

const nodeClasses = computed(() => ({
  'selected': props.selected,
  'dimmed': props.data?.dimmed,
  'has-checkpoint': props.hasCheckpoint,
  'is-collapsed': isCollapsed.value,
  'node-disabled': props.disabled
}))

// Collapse state from persistent ui_state (survives save/reload)
const isCollapsed = computed(() => props.data?.ui_state?.collapsed ?? false)

// Count nodes inside the container
const nodeCount = computed(() => {
  return props.data?.params?.subflow?.nodes?.length || 0
})

// Child node data for minimap preview
const childNodes = computed(() => {
  const nodes = props.data?.params?.subflow?.nodes || []
  return nodes.slice(0, 5).map(node => {
    const moduleId = node.data?.module || node.module || ''
    const icon = getNodeIcon(moduleId)
    const isUrl = isCustomUrlIcon(icon)
    return {
      id: node.id,
      moduleId,
      icon: isUrl ? null : icon,
      isUrl,
      url: isUrl ? icon.url : null,
      color: getCategoryColor(moduleId),
      label: getNodeLabel(moduleId) || moduleId.split('.').pop() || '?'
    }
  })
})

// Toggle collapse state and persist to node data
function toggleCollapse() {
  const newState = !isCollapsed.value
  emit('update:data', {
    ...props.data,
    ui_state: { ...(props.data?.ui_state || {}), collapsed: newState }
  })
}

// Handle double-click to enter edit mode
function handleDoubleClick() {
  emit('edit-container', {
    nodeId: props.id,
    containerId: props.id,
    subflow: props.data?.params?.subflow || { nodes: [], edges: [] }
  })
}
</script>

<style scoped>
.container-node {
  position: relative;
  width: var(--node-container-width, 90px);
  height: var(--node-container-height, 90px);
  transition: transform 0.2s ease;
}

.container-node:hover {
  transform: translateY(-2px);
}

/* Container shape - stacked box effect */
.container-shape {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 2px solid #8B5CF6;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.25);
  transition: all 0.2s ease;
  position: relative;
  z-index: 3;
}

.container-node:hover .container-shape {
  border-color: #A78BFA;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
}

.container-node.selected .container-shape {
  border-color: transparent;
}

.container-node.selected::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 16px;
  padding: 2px;
  background: linear-gradient(90deg, #8B5CF6, #A78BFA, #C4B5FD, #8B5CF6);
  background-size: 300% 100%;
  animation: border-flow 3s linear infinite;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  z-index: 2;
}

@keyframes border-flow {
  0% { background-position: 0% 50%; }
  100% { background-position: 300% 50%; }
}

/* Nested layers indicator */
.layers-indicator {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.layer {
  position: absolute;
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.5);
}

.layer-1 {
  inset: -4px;
  z-index: 1;
}

.layer-2 {
  inset: -8px;
  z-index: 0;
  border-color: rgba(139, 92, 246, 0.15);
}

/* Content */
.shape-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  z-index: 4;
}

.node-icon {
  color: #A78BFA;
}

.node-label {
  font-size: 11px;
  font-weight: 600;
  color: #f1f5f9;
  text-align: center;
  max-width: 70px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Minimap preview */
.minimap-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  align-items: center;
  max-width: 68px;
  padding: 2px;
}

.mini-node {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0.85;
  transition: opacity 0.2s;
}

.container-node:hover .mini-node {
  opacity: 1;
}

.mini-icon-img {
  width: 10px;
  height: 10px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

/* Node count badge */
.node-count-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  border: 2px solid #0F172A;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

/* Handles */
.handle {
  width: 10px !important;
  height: 10px !important;
  border: 2px solid #374151 !important;
  border-radius: 50% !important;
  z-index: 10;
}

.handle-hidden {
  opacity: 0 !important;
  pointer-events: none !important;
}

.handle-in {
  left: -5px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  background: #6B7280 !important;
}

.handle-out {
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

.container-node:hover .delete-btn { opacity: 1; }
.delete-btn:hover { transform: scale(1.2); background: #DC2626; }

/* Save as Template button */
.save-tpl-btn {
  position: absolute;
  top: -8px;
  left: 20px;
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

.container-node:hover .save-tpl-btn { opacity: 1; }
.save-tpl-btn:hover { transform: scale(1.15); background: linear-gradient(135deg, #A78BFA, #C084FC); }

/* Add button */
.add-btn {
  position: absolute;
  right: -16px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
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

.container-node:hover .add-btn { opacity: 1; }
.add-btn:hover { transform: translateY(-50%) scale(1.15); }

/* Edit hint */
.edit-hint {
  position: absolute;
  bottom: -24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 6px;
  font-size: 9px;
  color: #94a3b8;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.container-node:hover .edit-hint {
  opacity: 1;
}

/* Collapse button */
.collapse-btn {
  position: absolute;
  bottom: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #374151;
  border: 2px solid #1F2937;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 20;
  color: #94a3b8;
}

.container-node:hover .collapse-btn { opacity: 1; }
.collapse-btn:hover { transform: scale(1.2); background: #4B5563; color: white; }

/* Collapsed state */
.container-node.is-collapsed .container-shape {
  opacity: 0.7;
}

/* States */
.container-node.dimmed { opacity: 0.4; pointer-events: none; }

/* Checkpoint - red ripple effect */
.container-node.has-checkpoint .container-shape {
  border-color: #EF4444;
}

.container-node.has-checkpoint::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 18px;
  border: 2px solid #EF4444;
  animation: ripple-ring 2.5s ease-out infinite;
  pointer-events: none;
  z-index: 5;
}

.container-node.has-checkpoint:hover .container-shape {
  border-color: #6366F1;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

.container-node.has-checkpoint:hover::after {
  animation: none;
  opacity: 0;
}

/* ========== Disabled State ========== */
.container-node.node-disabled {
  cursor: not-allowed;
}

.container-node.node-disabled:hover {
  transform: none;
}

.container-node.node-disabled .handle {
  opacity: 0.4;
}

.container-node.node-disabled .add-btn {
  display: none;
}

.container-node.node-disabled .container-shape {
  opacity: 0.5;
  filter: grayscale(40%);
}

@keyframes ripple-ring {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.3); opacity: 0; }
}
</style>
