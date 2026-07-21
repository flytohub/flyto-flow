<template>
  <div class="divide-y divide-gray-700">
    <!-- Empty State -->
    <div v-if="!spans.length" class="p-8 text-center text-gray-400">
      <GitBranch :size="32" class="mx-auto mb-2 opacity-50" />
      <p>{{ $t('traces.waterfall.empty', 'No spans available') }}</p>
    </div>

    <!-- Span Rows -->
    <div
      v-for="span in sortedSpans"
      :key="span.spanId"
      @click="$emit('select', span)"
      class="flex items-center gap-4 px-4 py-3 cursor-pointer transition-colors"
      :class="[
        selectedSpan?.spanId === span.spanId
          ? 'bg-purple-900/20'
          : 'hover:bg-gray-700/30'
      ]"
    >
      <!-- Span Name -->
      <div class="w-40 flex-shrink-0">
        <div class="flex items-center gap-2">
          <StatusDot :status="span.status" />
          <span class="text-sm text-white truncate" :title="span.operationName">
            {{ span.operationName || span.stepId }}
          </span>
        </div>
        <p v-if="span.moduleId" class="text-xs text-gray-500 truncate mt-0.5">
          {{ span.moduleId }}
        </p>
      </div>

      <!-- Timeline Bar -->
      <div class="flex-1 relative h-6">
        <div class="absolute inset-0 bg-gray-700/30 rounded"></div>
        <div
          class="absolute h-full rounded transition-all"
          :class="getBarColor(span.status)"
          :style="getBarStyle(span)"
        ></div>
      </div>

      <!-- Duration -->
      <div class="w-20 text-right flex-shrink-0">
        <span class="text-sm text-gray-300">{{ formatDuration(span.durationMs) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { GitBranch } from 'lucide-vue-next'
import StatusDot from './StatusDot.vue'
import { formatDuration } from '@/utils/format'

const props = defineProps({
  spans: {
    type: Array,
    default: () => []
  },
  timelineData: {
    type: Object,
    default: () => ({ spans: [], minTime: 0, maxTime: 0, totalDuration: 0 })
  },
  selectedSpan: {
    type: Object,
    default: null
  }
})

defineEmits(['select'])

const { t } = useI18n()

// Sort spans by start time
const sortedSpans = computed(() => {
  return [...props.spans].sort((a, b) => {
    return new Date(a.startTime) - new Date(b.startTime)
  })
})

// Calculate bar position and width
function getBarStyle(span) {
  if (!props.timelineData.totalDuration) {
    return { left: '0%', width: '100%' }
  }

  const minTime = props.timelineData.minTime
  const totalDuration = props.timelineData.totalDuration

  const startTime = new Date(span.startTime).getTime()
  const duration = span.durationMs || 0

  const left = ((startTime - minTime) / totalDuration) * 100
  const width = Math.max((duration / totalDuration) * 100, 1) // Minimum 1% width

  return {
    left: `${Math.max(0, Math.min(left, 99))}%`,
    width: `${Math.max(1, Math.min(width, 100 - left))}%`
  }
}

// Get bar color based on status
function getBarColor(status) {
  const colors = {
    completed: 'bg-green-500/70',
    success: 'bg-green-500/70',
    failed: 'bg-red-500/70',
    error: 'bg-red-500/70',
    running: 'bg-blue-500/70',
    pending: 'bg-yellow-500/70'
  }
  return colors[status] || 'bg-gray-500/70'
}
</script>
