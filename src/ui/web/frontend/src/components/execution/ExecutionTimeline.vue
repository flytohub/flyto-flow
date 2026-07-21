<template>
  <div class="execution-timeline">
    <!-- Header -->
    <div class="timeline-header">
      <div class="header-left">
        <Clock :size="14" />
        <span class="title">{{ $t('execution.timeline', 'Execution Timeline') }}</span>
      </div>
      <div class="header-right">
        <span class="total-duration">{{ formatDuration(totalDuration) }}</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!nodes.length" class="empty-state">
      <Activity :size="24" class="empty-icon" />
      <p>{{ $t('execution.timeline.empty', 'No execution data') }}</p>
    </div>

    <!-- Timeline Rows -->
    <div v-else class="timeline-rows">
      <div
        v-for="node in sortedNodes"
        :key="node.id"
        class="timeline-row"
        :class="{ selected: selectedNodeId === node.id }"
        @click="$emit('select', node.id)"
      >
        <!-- Node Label -->
        <div class="node-info">
          <StatusDot :status="node.status" />
          <span class="node-label" :title="node.label">{{ node.label }}</span>
        </div>

        <!-- Timeline Bar Container -->
        <div class="bar-container">
          <div class="bar-background" />
          <div
            class="bar"
            :class="getBarClass(node.status)"
            :style="getBarStyle(node)"
          />
        </div>

        <!-- Duration -->
        <div class="duration">
          {{ formatDuration(node.durationMs) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Clock, Activity } from 'lucide-vue-next'
import { formatDuration } from '@/utils/format'
import StatusDot from '@/components/traces/StatusDot.vue'

const props = defineProps({
  nodes: {
    type: Array,
    default: () => []
    // Expected: [{ id, label, status, startedAt, durationMs }]
  },
  selectedNodeId: {
    type: String,
    default: null
  }
})

defineEmits(['select'])

const { t } = useI18n()

// Calculate timeline boundaries
const timelineData = computed(() => {
  if (!props.nodes.length) return { minTime: 0, maxTime: 0, totalDuration: 0 }

  const times = props.nodes
    .filter(n => n.startedAt)
    .map(n => ({
      start: new Date(n.startedAt).getTime(),
      end: new Date(n.startedAt).getTime() + (n.durationMs || 0)
    }))

  if (!times.length) return { minTime: 0, maxTime: 0, totalDuration: 0 }

  const minTime = Math.min(...times.map(t => t.start))
  const maxTime = Math.max(...times.map(t => t.end))
  const totalDuration = maxTime - minTime

  return { minTime, maxTime, totalDuration }
})

// Total workflow duration
const totalDuration = computed(() => {
  return timelineData.value.totalDuration
})

// Sort nodes by start time
const sortedNodes = computed(() => {
  return [...props.nodes].sort((a, b) => {
    const aTime = a.startedAt ? new Date(a.startedAt).getTime() : 0
    const bTime = b.startedAt ? new Date(b.startedAt).getTime() : 0
    return aTime - bTime
  })
})

// Calculate bar position and width
function getBarStyle(node) {
  if (!timelineData.value.totalDuration || !node.startedAt) {
    return { left: '0%', width: '100%' }
  }

  const { minTime, totalDuration } = timelineData.value
  const startTime = new Date(node.startedAt).getTime()
  const duration = node.durationMs || 0

  const left = ((startTime - minTime) / totalDuration) * 100
  const width = Math.max((duration / totalDuration) * 100, 1) // Minimum 1% width

  return {
    left: `${Math.max(0, Math.min(left, 99))}%`,
    width: `${Math.max(1, Math.min(width, 100 - left))}%`
  }
}

// Get bar color class based on status
function getBarClass(status) {
  const classes = {
    completed: 'bar-success',
    success: 'bar-success',
    failed: 'bar-error',
    error: 'bar-error',
    running: 'bar-running',
    pending: 'bar-pending'
  }
  return classes[status] || 'bar-default'
}
</script>

<style scoped>
.execution-timeline {
  display: flex;
  flex-direction: column;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid #334155;
  border-radius: 12px;
  overflow: hidden;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.5);
  border-bottom: 1px solid #334155;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
}

.title {
  font-size: 12px;
  font-weight: 600;
}

.total-duration {
  font-size: 11px;
  font-weight: 600;
  color: #8B5CF6;
  padding: 2px 8px;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 4px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  color: #64748b;
}

.empty-icon {
  opacity: 0.5;
  margin-bottom: 8px;
}

.empty-state p {
  margin: 0;
  font-size: 12px;
}

.timeline-rows {
  display: flex;
  flex-direction: column;
  max-height: 300px;
  overflow-y: auto;
}

.timeline-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
}

.timeline-row:last-child {
  border-bottom: none;
}

.timeline-row:hover {
  background: rgba(139, 92, 246, 0.1);
}

.timeline-row.selected {
  background: rgba(139, 92, 246, 0.15);
}

.node-info {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 120px;
  flex-shrink: 0;
}

.node-label {
  font-size: 11px;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-container {
  flex: 1;
  position: relative;
  height: 16px;
}

.bar-background {
  position: absolute;
  inset: 0;
  background: rgba(51, 65, 85, 0.4);
  border-radius: 4px;
}

.bar {
  position: absolute;
  top: 0;
  height: 100%;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.bar-success {
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.7), rgba(16, 185, 129, 0.5));
}

.bar-error {
  background: linear-gradient(90deg, rgba(239, 68, 68, 0.7), rgba(239, 68, 68, 0.5));
}

.bar-running {
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.7), rgba(139, 92, 246, 0.5));
  animation: pulse 1.5s ease-in-out infinite;
}

.bar-pending {
  background: linear-gradient(90deg, rgba(245, 158, 11, 0.7), rgba(245, 158, 11, 0.5));
}

.bar-default {
  background: linear-gradient(90deg, rgba(100, 116, 139, 0.7), rgba(100, 116, 139, 0.5));
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.duration {
  width: 60px;
  flex-shrink: 0;
  font-size: 10px;
  font-family: 'SF Mono', Monaco, monospace;
  color: #94a3b8;
  text-align: right;
}
</style>
