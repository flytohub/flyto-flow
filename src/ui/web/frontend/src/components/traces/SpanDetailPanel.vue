<template>
  <div class="p-4 space-y-4">
    <!-- Basic Info -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('traces.spanDetail.spanId', 'Span ID') }}</p>
        <p class="text-sm text-white font-mono truncate">{{ span.spanId }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('traces.spanDetail.operation', 'Operation') }}</p>
        <p class="text-sm text-white">{{ span.operationName || span.stepId }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('traces.spanDetail.module', 'Module') }}</p>
        <p class="text-sm text-white font-mono">{{ span.moduleId || '-' }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('traces.spanDetail.duration', 'Duration') }}</p>
        <p class="text-sm text-white">{{ formatDuration(span.durationMs) }}</p>
      </div>
    </div>

    <!-- Timing -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('traces.spanDetail.startTime', 'Start Time') }}</p>
        <p class="text-sm text-white">{{ formatTime(span.startTime) }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('traces.spanDetail.endTime', 'End Time') }}</p>
        <p class="text-sm text-white">{{ formatTime(span.endTime) }}</p>
      </div>
    </div>

    <!-- Status -->
    <div>
      <p class="text-xs text-gray-500 mb-1">{{ $t('traces.spanDetail.status', 'Status') }}</p>
      <StatusBadge :status="span.status" />
    </div>

    <!-- Error (if any) -->
    <div v-if="span.error" class="bg-red-900/20 border border-red-900/30 rounded-lg p-3">
      <p class="text-xs text-red-400 font-medium mb-1">{{ $t('traces.spanDetail.error', 'Error') }}</p>
      <p class="text-sm text-red-300">{{ span.error }}</p>
    </div>

    <!-- Tags -->
    <div v-if="hasTags">
      <p class="text-xs text-gray-500 mb-2">{{ $t('traces.spanDetail.tags', 'Tags') }}</p>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="(value, key) in span.tags"
          :key="key"
          class="inline-flex items-center px-2 py-1 bg-gray-700 rounded text-xs"
        >
          <span class="text-gray-400">{{ key }}:</span>
          <span class="text-white ml-1">{{ formatTagValue(value) }}</span>
        </span>
      </div>
    </div>

    <!-- Logs -->
    <div v-if="hasLogs">
      <p class="text-xs text-gray-500 mb-2">{{ $t('traces.spanDetail.logs', 'Logs') }}</p>
      <div class="bg-gray-900 rounded-lg p-3 max-h-48 overflow-y-auto">
        <div
          v-for="(log, index) in span.logs"
          :key="index"
          class="text-xs font-mono mb-1 last:mb-0"
        >
          <span class="text-gray-500">{{ formatLogTime(log.timestamp) }}</span>
          <span class="text-white ml-2">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import StatusBadge from './StatusBadge.vue'
import { formatDuration } from '@/utils/format'

const props = defineProps({
  span: {
    type: Object,
    required: true
  }
})

const { t } = useI18n()

const hasTags = computed(() => {
  return props.span.tags && Object.keys(props.span.tags).length > 0
})

const hasLogs = computed(() => {
  return props.span.logs && props.span.logs.length > 0
})

function formatTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString()
}

function formatLogTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

function formatTagValue(value) {
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}
</script>
