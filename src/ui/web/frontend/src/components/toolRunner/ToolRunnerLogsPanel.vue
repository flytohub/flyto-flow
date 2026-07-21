<template>
  <div class="logs-panel">
    <div class="panel-header">
      <Terminal :size="18" />
      <span>{{ $t('toolRunner.executionLogs') }}</span>
      <span v-if="executionTime" class="execution-time">
        <Clock :size="12" />
        {{ executionTime }}ms
      </span>
    </div>

    <div class="logs-content">
      <div
        v-for="log in logs"
        :key="log.id"
        class="log-entry"
        :class="log.type"
      >
        <span class="log-time">{{ log.time }}</span>
        <span class="log-step">{{ log.step }}</span>
        <span class="log-message">{{ log.message }}</span>
      </div>
      <div v-if="logs.length === 0" class="no-logs">
        {{ $t('toolRunner.noLogs') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { Terminal, Clock } from 'lucide-vue-next'

defineProps({
  logs: {
    type: Array,
    default: () => []
  },
  executionTime: {
    type: Number,
    default: null
  }
})
</script>

<style scoped>
.logs-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 16px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.5);
  border-bottom: 1px solid #334155;
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}

.execution-time {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 400;
  color: #64748b;
}

.logs-content {
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.log-entry {
  display: flex;
  gap: 10px;
  padding: 6px 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-size: 12px;
  background: rgba(15, 23, 42, 0.5);
}

.log-entry:last-child {
  margin-bottom: 0;
}

.log-time {
  font-family: 'Fira Code', monospace;
  font-size: 10px;
  color: #475569;
  min-width: 60px;
}

.log-step {
  font-weight: 500;
  color: #94a3b8;
  min-width: 80px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-message {
  color: #64748b;
  flex: 1;
}

.log-entry.info .log-message {
  color: #64748b;
}

.log-entry.success {
  background: rgba(16, 185, 129, 0.1);
}

.log-entry.success .log-step,
.log-entry.success .log-message {
  color: #10b981;
}

.log-entry.error {
  background: rgba(239, 68, 68, 0.1);
}

.log-entry.error .log-step,
.log-entry.error .log-message {
  color: #ef4444;
}

.log-entry.warning {
  background: rgba(245, 158, 11, 0.1);
}

.log-entry.warning .log-step,
.log-entry.warning .log-message {
  color: #f59e0b;
}

.no-logs {
  text-align: center;
  padding: 20px;
  font-size: 12px;
  color: #64748b;
}
</style>
