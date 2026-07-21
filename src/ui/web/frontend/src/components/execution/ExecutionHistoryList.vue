<template>
  <div class="execution-list">
    <div
      v-for="execution in executions"
      :key="execution.id"
      class="execution-item"
      :class="{
        'is-selected': selectedExecutionId === execution.id,
        [`status-${execution.status}`]: true
      }"
      @click="$emit('select', execution)"
    >
      <div class="execution-status">
        <div class="status-icon" :style="{ backgroundColor: execution.statusColor }">
          <CheckCircle v-if="execution.status === 'success'" :size="12" />
          <XCircle v-else-if="execution.status === 'failed'" :size="12" />
          <Loader2 v-else-if="execution.status === 'running'" :size="12" class="animate-spin" />
          <Clock v-else-if="execution.status === 'pending'" :size="12" />
          <Ban v-else :size="12" />
        </div>
      </div>

      <div class="execution-info">
        <div class="execution-time">
          {{ execution.formattedStartTime }}
        </div>
        <div class="execution-meta">
          <span class="duration">
            <Timer :size="12" />
            {{ execution.formattedDuration }}
          </span>
          <span v-if="execution.errorMessage" class="error-hint" :title="execution.errorMessage">
            <AlertTriangle :size="12" />
            {{ t('executionHistory.hasError', 'Error') }}
          </span>
        </div>
      </div>

      <div class="execution-actions">
        <ChevronRight :size="16" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import {
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Timer,
  AlertTriangle,
  ChevronRight,
  Ban
} from 'lucide-vue-next'

const { t } = useI18n()

defineProps({
  executions: { type: Array, required: true },
  selectedExecutionId: { type: String, default: null },
})

defineEmits(['select'])
</script>

<style scoped>
.execution-list {
  padding: 8px;
}

.execution-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 6px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.execution-item:hover {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(139, 92, 246, 0.3);
}

.execution-item.is-selected {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.5);
}

.execution-status {
  flex-shrink: 0;
}

.status-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.execution-info {
  flex: 1;
  min-width: 0;
}

.execution-time {
  font-size: 13px;
  font-weight: 500;
  color: #e2e8f0;
  margin-bottom: 4px;
}

.execution-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
  color: #64748b;
}

.execution-meta .duration {
  display: flex;
  align-items: center;
  gap: 4px;
}

.execution-meta .error-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #ef4444;
}

.execution-actions {
  color: #64748b;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
