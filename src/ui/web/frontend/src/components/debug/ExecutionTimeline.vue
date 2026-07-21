<template>
  <div class="bg-gray-800 rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
      <div class="flex items-center gap-2">
        <Clock :size="18" class="text-purple-400" />
        <h3 class="text-sm font-medium text-white">{{ $t('debug.timeline') }}</h3>
      </div>
      <div v-if="summary" class="flex items-center gap-4 text-xs text-gray-400">
        <span>{{ summary.completed }}/{{ summary.total }} {{ $t('debug.completed') }}</span>
        <span v-if="summary.failed > 0" class="text-red-400">
          {{ summary.failed }} {{ $t('debug.failed') }}
        </span>
        <span>{{ formatDuration(summary.totalDuration) }}</span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!events.length" class="p-8 text-center text-gray-400">
      <Activity :size="32" class="mx-auto mb-2 opacity-50" />
      <p>{{ $t('debug.noEvents') }}</p>
    </div>

    <!-- Timeline -->
    <div v-else class="p-4">
      <!-- Horizontal scrollable timeline -->
      <div class="flex gap-2 overflow-x-auto pb-2" ref="timelineRef">
        <div
          v-for="(event, index) in events"
          :key="event.nodeId || index"
          @click="selectEvent(index)"
          class="flex-shrink-0 cursor-pointer transition-all"
          :class="[
            selectedIndex === index
              ? 'ring-2 ring-purple-500'
              : 'hover:ring-1 hover:ring-gray-600'
          ]"
        >
          <!-- Event Card -->
          <div
            class="w-32 p-3 rounded-lg"
            :class="getEventCardClass(event.status)"
          >
            <!-- Status Icon -->
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-1.5">
                <component :is="getStatusIcon(event.status)" :size="14" :class="getStatusColor(event.status)" />
                <span class="text-xs text-gray-400">{{ index + 1 }}</span>
              </div>
              <span class="text-xs text-gray-500">{{ formatDuration(event.durationMs) }}</span>
            </div>

            <!-- Node Name -->
            <p class="text-sm text-white truncate" :title="event.nodeId || event.stepId">
              {{ getShortName(event.nodeId || event.stepId) }}
            </p>
            <p v-if="event.moduleId" class="text-xs text-gray-500 truncate mt-0.5">
              {{ event.moduleId }}
            </p>
          </div>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="mt-4 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          class="h-full transition-all duration-300"
          :class="progressBarClass"
          :style="{ width: progressWidth + '%' }"
        ></div>
      </div>

      <!-- Step Navigation -->
      <div class="flex items-center justify-between mt-4">
        <button
          @click="$emit('prev')"
          :disabled="selectedIndex === 0"
          class="flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg transition-colors"
          :class="selectedIndex === 0 ? 'text-gray-600 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-700'"
          aria-label="Previous step"
        >
          <ChevronLeft :size="16" />
          {{ $t('debug.prev') }}
        </button>
        <span class="text-sm text-gray-400">
          {{ selectedIndex + 1 }} / {{ events.length }}
        </span>
        <button
          @click="$emit('next')"
          :disabled="selectedIndex === events.length - 1"
          class="flex items-center gap-1 px-3 py-1.5 text-sm rounded-lg transition-colors"
          :class="selectedIndex === events.length - 1 ? 'text-gray-600 cursor-not-allowed' : 'text-gray-300 hover:bg-gray-700'"
          aria-label="Next step"
        >
          {{ $t('debug.next') }}
          <ChevronRight :size="16" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Clock,
  Activity,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Loader,
  Circle
} from 'lucide-vue-next'
import { formatDuration } from '@/utils/format'

const props = defineProps({
  events: {
    type: Array,
    default: () => []
  },
  selectedIndex: {
    type: Number,
    default: 0
  },
  summary: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['select', 'prev', 'next'])
const { t } = useI18n()

const timelineRef = ref(null)

// Watch for selected index changes to scroll into view
watch(() => props.selectedIndex, async (newIndex) => {
  await nextTick()
  if (timelineRef.value) {
    const cards = timelineRef.value.children
    if (cards[newIndex]) {
      cards[newIndex].scrollIntoView({ behavior: 'smooth', inline: 'center' })
    }
  }
})

// Computed progress
const progressWidth = computed(() => {
  if (!props.events.length) return 0
  const completed = props.events.filter(e =>
    e.status === 'success' || e.status === 'completed'
  ).length
  return (completed / props.events.length) * 100
})

const progressBarClass = computed(() => {
  const hasFailed = props.events.some(e => e.status === 'failed' || e.status === 'error')
  if (hasFailed) return 'bg-red-500'
  if (progressWidth.value === 100) return 'bg-green-500'
  return 'bg-purple-500'
})

function selectEvent(index) {
  emit('select', index)
}

function getEventCardClass(status) {
  const classes = {
    success: 'bg-green-900/20 border border-green-800/30',
    completed: 'bg-green-900/20 border border-green-800/30',
    failed: 'bg-red-900/20 border border-red-800/30',
    error: 'bg-red-900/20 border border-red-800/30',
    running: 'bg-blue-900/20 border border-blue-800/30',
    pending: 'bg-gray-700/30 border border-gray-700'
  }
  return classes[status] || 'bg-gray-700/30 border border-gray-700'
}

function getStatusIcon(status) {
  const icons = {
    success: CheckCircle,
    completed: CheckCircle,
    failed: XCircle,
    error: XCircle,
    running: Loader,
    pending: Circle
  }
  return icons[status] || Circle
}

function getStatusColor(status) {
  const colors = {
    success: 'text-green-400',
    completed: 'text-green-400',
    failed: 'text-red-400',
    error: 'text-red-400',
    running: 'text-blue-400 animate-spin',
    pending: 'text-gray-500'
  }
  return colors[status] || 'text-gray-500'
}

function getShortName(name) {
  if (!name) return 'Step'
  // Get last part of node_id (e.g., "workflow.node_1" -> "node_1")
  const parts = name.split('.')
  return parts[parts.length - 1]
}
</script>
