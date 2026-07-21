<template>
  <div class="timeline-panel">
    <div class="timeline-header">
      <button class="back-btn" @click="$emit('back')" aria-label="Back">
        <ChevronLeft :size="18" />
        <span>{{ t('common.back', 'Back') }}</span>
      </button>
      <div class="timeline-title">
        <span class="execution-id">{{ execution.id.slice(0, 8) }}...</span>
        <div class="timeline-status" :style="{ color: timeline.statusColor }">
          {{ timeline.status }}
        </div>
      </div>
    </div>

    <!-- Timeline Stats -->
    <div class="timeline-stats">
      <div class="timeline-stat">
        <span class="stat-value">{{ timeline.completedSteps }}/{{ timeline.totalSteps }}</span>
        <span class="stat-label">{{ t('executionHistory.steps', 'Steps') }}</span>
      </div>
      <div class="timeline-stat">
        <span class="stat-value">{{ timeline.formattedDuration }}</span>
        <span class="stat-label">{{ t('executionHistory.duration', 'Duration') }}</span>
      </div>
    </div>

    <!-- Timeline Loading -->
    <div v-if="loading" class="timeline-loading">
      <Loader2 :size="24" class="animate-spin" />
    </div>

    <!-- Timeline Events -->
    <div v-else class="timeline-events">
      <div
        v-for="(event, index) in timeline.events"
        :key="`${event.nodeId}-${index}`"
        class="timeline-event"
        :class="[`event-${event.eventType}`]"
        @click="$emit('event-click', event)"
      >
        <div class="event-line">
          <div class="event-dot" :style="{ backgroundColor: event.statusColor }"></div>
          <div v-if="index < timeline.events.length - 1" class="event-connector"></div>
        </div>

        <div class="event-content">
          <div class="event-header">
            <span class="event-module">{{ event.moduleId || event.nodeId }}</span>
            <span class="event-duration">{{ event.formattedDuration }}</span>
          </div>

          <div class="event-type">{{ event.eventType }}</div>

          <!-- Error Display -->
          <div v-if="event.error" class="event-error">
            <AlertTriangle :size="14" />
            <span>{{ event.error }}</span>
          </div>

          <!-- Output Preview -->
          <div v-if="event.outputs && showOutputPreview" class="event-output">
            <button class="toggle-output" @click.stop="toggleOutput(event)" aria-label="Toggle output">
              <Code :size="12" />
              {{ expandedOutputs[event.nodeId] ? t('common.hide', 'Hide') : t('common.show', 'Show') }}
            </button>
            <pre v-if="expandedOutputs[event.nodeId]" class="output-content">{{ formatOutput(event.outputs) }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Retry Button for Failed Executions -->
    <div v-if="timeline.status === 'failed' && timeline.failedStep" class="timeline-actions">
      <button class="retry-btn" @click="$emit('retry')" aria-label="Retry">
        <RotateCcw :size="16" />
        {{ t('executionHistory.retryFromFailed', 'Retry from failed step') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ChevronLeft,
  Loader2,
  AlertTriangle,
  Code,
  RotateCcw
} from 'lucide-vue-next'

const { t } = useI18n()

defineProps({
  execution: { type: Object, required: true },
  timeline: { type: Object, required: true },
  loading: { type: Boolean, default: false },
  showOutputPreview: { type: Boolean, default: true },
})

defineEmits(['back', 'event-click', 'retry'])

const expandedOutputs = ref({})

function toggleOutput(event) {
  expandedOutputs.value[event.nodeId] = !expandedOutputs.value[event.nodeId]
}

function formatOutput(output) {
  try {
    return JSON.stringify(output, null, 2)
  } catch {
    return String(output)
  }
}
</script>

<style scoped>
.timeline-panel {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(99, 102, 241, 0.04) 100%);
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(71, 85, 105, 0.2);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 6px;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(71, 85, 105, 0.4);
  color: #e2e8f0;
}

.timeline-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.execution-id {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  font-family: 'JetBrains Mono', monospace;
}

.timeline-status {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.timeline-stats {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.6);
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
}

.timeline-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.timeline-stat .stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
}

.timeline-stat .stat-label {
  font-size: 11px;
  color: #64748b;
}

.timeline-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #8B5CF6;
}

.timeline-events {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.timeline-event {
  display: flex;
  gap: 12px;
  cursor: pointer;
}

.event-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
}

.event-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 8px currentColor;
}

.event-connector {
  width: 2px;
  flex: 1;
  min-height: 20px;
  background: rgba(71, 85, 105, 0.4);
  margin: 4px 0;
}

.event-content {
  flex: 1;
  padding-bottom: 16px;
  min-width: 0;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.event-module {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-duration {
  font-size: 11px;
  color: #8B5CF6;
  font-weight: 500;
}

.event-type {
  font-size: 11px;
  color: #64748b;
  text-transform: capitalize;
  margin-bottom: 6px;
}

.event-error {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 10px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  margin-top: 8px;
}

.event-error svg {
  color: #ef4444;
  flex-shrink: 0;
  margin-top: 1px;
}

.event-error span {
  font-size: 12px;
  color: #fca5a5;
  word-break: break-word;
}

.event-output {
  margin-top: 8px;
}

.toggle-output {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(71, 85, 105, 0.2);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 4px;
  color: #94a3b8;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-output:hover {
  background: rgba(71, 85, 105, 0.4);
  color: #e2e8f0;
}

.output-content {
  margin-top: 8px;
  padding: 10px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #94a3b8;
  overflow-x: auto;
  max-height: 200px;
  white-space: pre-wrap;
  word-break: break-word;
}

.timeline-actions {
  padding: 12px 16px;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
  background: rgba(15, 23, 42, 0.8);
}

.retry-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  transform: translateY(-1px);
}

.timeline-events::-webkit-scrollbar {
  width: 6px;
}

.timeline-events::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
}

.timeline-events::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.4);
  border-radius: 3px;
}

.timeline-events::-webkit-scrollbar-thumb:hover {
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
