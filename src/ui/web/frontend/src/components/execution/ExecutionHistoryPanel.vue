<template>
  <div class="execution-history-panel" :class="{ 'is-loading': loading }">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-left">
        <History :size="20" class="header-icon" />
        <h3>{{ t('executionHistory.title', 'Execution History') }}</h3>
        <span v-if="stats" class="stats-badge">
          {{ stats.total_executions }} {{ t('executionHistory.runs', 'runs') }}
        </span>
      </div>
      <div class="header-actions">
        <button
          class="action-btn"
          @click="handleRefresh"
          :disabled="loading"
          :title="t('common.refresh', 'Refresh')"
        >
          <RefreshCw :size="16" :class="{ 'animate-spin': loading }" />
        </button>
        <button
          v-if="onClose"
          class="action-btn close"
          @click="onClose"
          :title="t('common.close', 'Close')"
        >
          <X :size="16" />
        </button>
      </div>
    </div>

    <!-- Stats Bar -->
    <div v-if="stats && stats.total_executions > 0" class="stats-bar">
      <div class="stat-item success">
        <CheckCircle :size="14" />
        <span>{{ stats.success_rate }}%</span>
        <span class="stat-label">{{ t('executionHistory.successRate', 'Success') }}</span>
      </div>
      <div class="stat-item duration">
        <Clock :size="14" />
        <span>{{ formatDuration(stats.average_duration_ms) }}</span>
        <span class="stat-label">{{ t('executionHistory.avgDuration', 'Avg') }}</span>
      </div>
      <div v-if="stats.failure_count > 0" class="stat-item failed">
        <XCircle :size="14" />
        <span>{{ stats.failure_count }}</span>
        <span class="stat-label">{{ t('executionHistory.failed', 'Failed') }}</span>
      </div>
    </div>

    <!-- Content -->
    <div class="panel-content">
      <!-- Loading State -->
      <div v-if="loading && !hasExecutions" class="loading-state">
        <Loader2 :size="32" class="animate-spin" />
        <span>{{ t('executionHistory.loading', 'Loading history...') }}</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="!hasExecutions" class="empty-state">
        <PlayCircle :size="48" />
        <p>{{ t('executionHistory.noExecutions', 'No executions yet') }}</p>
        <span>{{ t('executionHistory.runWorkflow', 'Run the workflow to see execution history') }}</span>
      </div>

      <!-- Execution List -->
      <ExecutionHistoryList
        v-else
        :executions="executions"
        :selected-execution-id="selectedExecution?.id"
        @select="handleSelectExecution"
      />
    </div>

    <!-- Timeline Panel (slides in when execution is selected) -->
    <Transition name="slide">
      <ExecutionHistoryDetail
        v-if="selectedExecution && timeline"
        :execution="selectedExecution"
        :timeline="timeline"
        :loading="timelineLoading"
        :show-output-preview="showOutputPreview"
        @back="handleClearSelection"
        @event-click="handleEventClick"
        @retry="handleRetry"
      />
    </Transition>

    <!-- Error Display -->
    <div v-if="error" class="error-banner">
      <AlertCircle :size="16" />
      <span>{{ error }}</span>
      <button @click="error = null">
        <X :size="14" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  History,
  RefreshCw,
  X,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  PlayCircle,
  AlertCircle
} from 'lucide-vue-next'
import { useExecutionHistory } from '@/composables/useExecutionHistory'
import ExecutionHistoryList from './ExecutionHistoryList.vue'
import ExecutionHistoryDetail from './ExecutionHistoryDetail.vue'

const { t } = useI18n()

const props = defineProps({
  workflowId: {
    type: String,
    required: true
  },
  onClose: {
    type: Function,
    default: null
  },
  showOutputPreview: {
    type: Boolean,
    default: true
  },
  autoRefreshInterval: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['select', 'retry', 'event-click'])

const {
  executions,
  selectedExecution,
  timeline,
  stats,
  loading,
  timelineLoading,
  error,
  hasExecutions,
  fetchHistory,
  fetchStats,
  selectExecution,
  clearSelection,
  refresh,
  formatDuration
} = useExecutionHistory()

let refreshTimer = null

async function handleRefresh() {
  await refresh(props.workflowId)
}

async function handleSelectExecution(execution) {
  await selectExecution(execution)
  emit('select', execution)
}

function handleClearSelection() {
  clearSelection()
}

function handleEventClick(event) {
  emit('event-click', event)
}

function handleRetry() {
  if (selectedExecution.value && timeline.value?.failedStep) {
    emit('retry', {
      executionId: selectedExecution.value.id,
      nodeId: timeline.value.failedStep
    })
  }
}

function setupAutoRefresh() {
  if (props.autoRefreshInterval > 0) {
    refreshTimer = setInterval(() => {
      // Only auto-refresh if no execution is selected AND there are running executions
      if (!selectedExecution.value) {
        refresh(props.workflowId)
      }
    }, props.autoRefreshInterval)
  }
}

function clearAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(async () => {
  if (props.workflowId) {
    await Promise.all([
      fetchHistory(props.workflowId),
      fetchStats(props.workflowId)
    ])
    setupAutoRefresh()
  }
})

watch(() => props.workflowId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    clearSelection()
    await refresh(newId)
  }
})

watch(() => props.autoRefreshInterval, (newInterval) => {
  clearAutoRefresh()
  if (newInterval > 0) {
    setupAutoRefresh()
  }
})

onUnmounted(() => {
  clearAutoRefresh()
})
</script>

<style scoped>
.execution-history-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(99, 102, 241, 0.04) 100%);
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  color: #8B5CF6;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}

.stats-badge {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
  background: rgba(71, 85, 105, 0.3);
  border-radius: 10px;
}

.header-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  background: rgba(71, 85, 105, 0.2);
  border: 1px solid rgba(71, 85, 105, 0.3);
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: rgba(71, 85, 105, 0.4);
  color: #e2e8f0;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.close:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.stats-bar {
  display: flex;
  gap: 16px;
  padding: 10px 16px;
  background: rgba(15, 23, 42, 0.6);
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
}

.stat-item.success { color: #10B981; }
.stat-item.failed { color: #ef4444; }
.stat-item.duration { color: #8B5CF6; }

.stat-label {
  color: #64748b;
  font-size: 11px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
  gap: 12px;
  color: #64748b;
  text-align: center;
  padding: 24px;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: #94a3b8;
}

.empty-state span {
  font-size: 12px;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(239, 68, 68, 0.1);
  border-top: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  font-size: 12px;
}

.error-banner svg:first-child {
  color: #ef4444;
  flex-shrink: 0;
}

.error-banner span {
  flex: 1;
}

.error-banner button {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
}

.error-banner button:hover {
  color: #e2e8f0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from {
  transform: translateX(100%);
}

.slide-leave-to {
  transform: translateX(100%);
}

.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
}

.panel-content::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.4);
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.6);
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
