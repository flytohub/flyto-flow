<template>
  <div class="checkpoint-list" role="listbox" :aria-label="listLabel">
    <div
      v-for="checkpoint in checkpoints"
      :key="checkpoint.id"
      class="checkpoint-item"
      :class="{
        selected: modelValue === checkpoint.id,
        recommended: checkpoint.id === recommended,
        error: checkpoint.hasError
      }"
      role="option"
      :aria-selected="modelValue === checkpoint.id"
      @click="$emit('update:modelValue', checkpoint.id)"
    >
      <div class="checkpoint-icon">
        <AlertCircle v-if="checkpoint.hasError" :size="16" aria-hidden="true" />
        <CheckCircle v-else-if="checkpoint.type === 'nodeComplete'" :size="16" aria-hidden="true" />
        <Circle v-else :size="16" aria-hidden="true" />
      </div>

      <div class="checkpoint-info">
        <div class="checkpoint-header">
          <span class="checkpoint-node">{{ checkpoint.nodeId }}</span>
          <span v-if="checkpoint.id === recommended" class="recommended-badge">
            {{ recommendedLabel }}
          </span>
        </div>
        <div class="checkpoint-meta">
          <span class="checkpoint-type">{{ formatType(checkpoint.type) }}</span>
          <span class="checkpoint-time">{{ formatTime(checkpoint.timestamp) }}</span>
        </div>
      </div>

      <div class="checkpoint-select">
        <div class="radio-indicator" :class="{ active: modelValue === checkpoint.id }"></div>
      </div>
    </div>

    <div v-if="checkpoints.length === 0" class="empty-state">
      <FileX :size="24" aria-hidden="true" />
      <span>{{ emptyLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { AlertCircle, CheckCircle, Circle, FileX } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  checkpoints: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: String,
    default: null
  },
  recommended: {
    type: String,
    default: null
  }
})

defineEmits(['update:modelValue'])

const listLabel = computed(() => t('execution.checkpoints.list', 'Available checkpoints'))
const recommendedLabel = computed(() => t('execution.checkpoints.recommended', 'Recommended'))
const emptyLabel = computed(() => t('execution.checkpoints.empty', 'No checkpoints available'))

const TYPE_LABELS = {
  nodeStart: 'Node Start',
  nodeComplete: 'Node Complete',
  error: 'Error',
  manual: 'Manual'
}

function formatType(type) {
  return TYPE_LABELS[type] || type
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.checkpoint-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
  padding: 4px;
}

.checkpoint-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.checkpoint-item:hover {
  background: rgba(71, 85, 105, 0.2);
  border-color: rgba(71, 85, 105, 0.5);
}

.checkpoint-item.selected {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.5);
}

.checkpoint-item.recommended {
  border-color: rgba(16, 185, 129, 0.5);
}

.checkpoint-item.error .checkpoint-icon {
  color: #ef4444;
}

.checkpoint-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: rgba(71, 85, 105, 0.3);
  color: #94a3b8;
}

.checkpoint-item.selected .checkpoint-icon {
  background: rgba(139, 92, 246, 0.2);
  color: #8B5CF6;
}

.checkpoint-info {
  flex: 1;
  min-width: 0;
}

.checkpoint-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.checkpoint-node {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recommended-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.checkpoint-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: #64748b;
}

.checkpoint-type {
  color: #94a3b8;
}

.checkpoint-select {
  display: flex;
  align-items: center;
}

.radio-indicator {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid rgba(71, 85, 105, 0.5);
  transition: all 0.2s;
}

.radio-indicator.active {
  border-color: #8B5CF6;
  background: #8B5CF6;
  box-shadow: inset 0 0 0 3px rgba(15, 23, 42, 0.8);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  color: #64748b;
  text-align: center;
}

.checkpoint-list::-webkit-scrollbar {
  width: 6px;
}

.checkpoint-list::-webkit-scrollbar-track {
  background: transparent;
}

.checkpoint-list::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.4);
  border-radius: 3px;
}

.checkpoint-list::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.6);
}
</style>
