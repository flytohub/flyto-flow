<template>
  <Transition name="action-bar">
    <div v-if="selectedNode" class="node-action-bar">
      <!-- Node info -->
      <div class="node-info">
        <component :is="getNodeIcon(selectedNode.data?.module)" :size="16" class="node-icon" />
        <span class="node-label">{{ resolveModuleLabel(selectedNode.data?.module, modulesStore) || selectedNode.id }}</span>
      </div>

      <!-- Action buttons -->
      <div class="action-buttons">
        <!-- Disable/Enable toggle -->
        <button
          class="action-btn"
          :class="{ 'disabled-state': isDisabled }"
          @click="$emit('toggle-disabled', selectedNode.id)"
          :title="isDisabled ? $t('workflow.enableNode') : $t('workflow.disableNode')"
        >
          <CircleSlash v-if="!isDisabled" :size="16" />
          <CirclePlay v-else :size="16" />
          <span>{{ isDisabled ? $t('workflow.enable') : $t('workflow.disable') }}</span>
        </button>

        <!-- Checkpoint toggle (only for paid users) -->
        <button
          v-if="canUseCheckpoint"
          class="action-btn"
          :class="{ 'active': hasCheckpoint }"
          @click="$emit('toggle-checkpoint', selectedNode.id)"
          :title="hasCheckpoint ? $t('debug.checkpoint.removeHint') : $t('debug.checkpoint.addHint')"
        >
          <CirclePause :size="16" />
          <span>{{ hasCheckpoint ? $t('debug.checkpoint.remove') : $t('debug.checkpoint.add') }}</span>
        </button>

        <!-- Collapse/Expand toggle -->
        <button
          class="action-btn"
          :class="{ 'collapsed-state': isCollapsed }"
          @click="$emit('toggle-collapse', selectedNode.id)"
          :title="isCollapsed ? $t('workflow.expandNode', 'Expand') : $t('workflow.collapseNode', 'Collapse')"
        >
          <Maximize2 v-if="isCollapsed" :size="16" />
          <Minimize2 v-else :size="16" />
          <span>{{ isCollapsed ? $t('workflow.expand', 'Expand') : $t('workflow.collapse', 'Collapse') }}</span>
        </button>

        <!-- Data Pinning toggle -->
        <button
          v-if="canPin"
          class="action-btn"
          :class="{ 'pinned': isPinned }"
          @click="$emit('toggle-pin', selectedNode.id)"
          :title="isPinned ? $t('workflow.unpinData') : $t('workflow.pinData')"
        >
          <Pin :size="16" />
          <span>{{ isPinned ? $t('workflow.unpin') : $t('workflow.pin') }}</span>
        </button>

        <!-- Add/Edit Description -->
        <button
          class="action-btn"
          :class="{ 'has-note': hasDescription }"
          @click="$emit('edit-note', selectedNode.id)"
          :title="hasDescription ? $t('workflow.editDescription', 'Edit Description') : $t('workflow.addDescription', 'Add Description')"
        >
          <MessageSquare :size="16" />
          <span>{{ hasDescription ? $t('common.edit', 'Edit') : $t('workflow.addDescription', 'Desc') }}</span>
        </button>

        <!-- Delete node -->
        <button
          class="action-btn danger"
          @click="$emit('delete-node', selectedNode.id)"
          :title="$t('debug.checkpoint.deleteNodeHint')"
        >
          <Trash2 :size="16" />
          <span>{{ $t('debug.checkpoint.deleteNode') }}</span>
        </button>
      </div>

      <!-- Close button -->
      <button class="close-btn" @click="$emit('close')" :title="$t('common.close')">
        <X :size="14" />
      </button>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { CirclePause, CircleSlash, CirclePlay, Pin, Trash2, X, Minimize2, Maximize2, MessageSquare } from 'lucide-vue-next'
import { useNodeStyles } from '../../composables/useNodeStyles'
import { useModulesStore } from '@/stores/modulesStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'

const { getNodeIcon } = useNodeStyles()
const modulesStore = useModulesStore()

const props = defineProps({
  selectedNode: {
    type: Object,
    default: null
  },
  checkpoints: {
    type: Array,
    default: () => []
  },
  // Whether user can use checkpoint feature (paid feature)
  canUseCheckpoint: {
    type: Boolean,
    default: false
  },
  // Whether user can use data pinning feature (paid feature)
  canUseDataPinning: {
    type: Boolean,
    default: false
  },
  // Whether the node has output data that can be pinned
  hasNodeOutput: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle-checkpoint', 'toggle-pin', 'toggle-disabled', 'toggle-collapse', 'edit-note', 'delete-node', 'close'])

const hasCheckpoint = computed(() => {
  if (!props.selectedNode) return false
  return props.checkpoints.includes(props.selectedNode.id)
})

// Disabled state
const isDisabled = computed(() => props.selectedNode?.data?.disabled || false)

// Collapsed state
const isCollapsed = computed(() => props.selectedNode?.data?.collapsed || false)

// Data Pinning computed properties
const isPinned = computed(() => props.selectedNode?.data?.isPinned || false)
const canPin = computed(() => {
  // Can pin if: feature enabled AND (node has execution output OR is already pinned)
  return props.canUseDataPinning && (props.hasNodeOutput || isPinned.value)
})

// Description state
const hasDescription = computed(() => Boolean(props.selectedNode?.data?.description))
</script>

<style scoped>
.node-action-bar {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.node-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 12px;
  border-right: 1px solid #334155;
}

.node-icon {
  color: #8b5cf6;
}

.node-label {
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid #475569;
  border-radius: 8px;
  color: #cbd5e1;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  border-color: #64748b;
  color: #f1f5f9;
}

.action-btn.active {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

.action-btn.active:hover {
  background: rgba(239, 68, 68, 0.3);
}

/* Pinned state (yellow) */
.action-btn.pinned {
  background: rgba(234, 179, 8, 0.2);
  border-color: #EAB308;
  color: #EAB308;
}

.action-btn.pinned:hover {
  background: rgba(234, 179, 8, 0.3);
}

.action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

/* Disabled state (gray/orange) */
.action-btn.disabled-state {
  background: rgba(249, 115, 22, 0.2);
  border-color: #F97316;
  color: #F97316;
}

.action-btn.disabled-state:hover {
  background: rgba(249, 115, 22, 0.3);
}

/* Collapsed state (blue) */
.action-btn.collapsed-state {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3B82F6;
  color: #3B82F6;
}

.action-btn.collapsed-state:hover {
  background: rgba(59, 130, 246, 0.3);
}

/* Has note state (purple) */
.action-btn.has-note {
  background: rgba(139, 92, 246, 0.2);
  border-color: #8B5CF6;
  color: #8B5CF6;
}

.action-btn.has-note:hover {
  background: rgba(139, 92, 246, 0.3);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-left: 4px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #f1f5f9;
}

/* Transition animation */
.action-bar-enter-active,
.action-bar-leave-active {
  transition: all 0.2s ease;
}

.action-bar-enter-from,
.action-bar-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
