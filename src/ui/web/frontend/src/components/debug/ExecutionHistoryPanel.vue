<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-x-full"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 translate-x-full"
    >
      <div
        v-if="isOpen"
        class="fixed top-0 right-0 h-full w-[520px] bg-gray-900 border-l border-gray-700 shadow-2xl z-40 flex flex-col"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-green-900/20">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-green-600/20 rounded-lg">
              <History :size="20" class="text-green-400" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ $t('executionHistory.title') }}</h3>
              <p class="text-xs text-gray-400">{{ workflowName }}</p>
            </div>
          </div>
          <button
            @click="$emit('close')"
            class="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X :size="20" />
          </button>
        </div>

        <!-- Filters -->
        <ExecutionHistoryFilters
          :result-count="filteredExecutions.length"
          :initial-filters="currentFilters"
          @filter-change="handleFilterChange"
        />

        <!-- Loading State -->
        <div v-if="isLoading" class="flex-1 flex items-center justify-center">
          <Loader :size="32" class="text-green-400 animate-spin" />
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredExecutions.length === 0" class="flex-1 flex flex-col items-center justify-center text-gray-400">
          <History :size="48" class="mb-3 opacity-50" />
          <p class="text-sm">{{ $t('executionHistory.noExecutions') }}</p>
          <p class="text-xs mt-1">{{ $t('executionHistory.runWorkflow') }}</p>
        </div>

        <!-- Executions List -->
        <div v-else class="flex-1 overflow-auto">
          <div
            v-for="execution in filteredExecutions"
            :key="execution.id"
            @click="handleSelectExecution(execution)"
            class="px-4 py-3 border-b border-gray-700/50 cursor-pointer transition-colors hover:bg-gray-800/50"
            :class="{ 'bg-green-900/20': selectedExecutionId === execution.id }"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-2">
                <!-- Status Icon -->
                <component
                  :is="getStatusIcon(execution.status)"
                  :size="16"
                  :class="getStatusColor(execution.status)"
                />
                <span class="text-sm font-mono text-gray-300">
                  {{ execution.id.slice(0, 8) }}...
                </span>
              </div>
              <span class="text-xs text-gray-500">
                {{ formatTime(execution.startedAt) }}
              </span>
            </div>

            <div class="flex items-center justify-between text-xs">
              <span :class="getStatusColor(execution.status)">
                {{ $t(`executionHistory.status${capitalize(execution.status)}`) }}
              </span>
              <span class="text-gray-500">
                {{ formatDuration(execution.duration) }}
              </span>
            </div>

            <!-- Error Message Preview -->
            <p
              v-if="execution.status === 'failed' && execution.error"
              class="text-xs text-red-400 mt-2 line-clamp-2"
            >
              {{ execution.error }}
            </p>

            <!-- Quick Actions -->
            <div class="flex items-center gap-2 mt-2">
              <button
                @click.stop="handleReplay(execution)"
                class="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
                aria-label="Replay"
              >
                <RotateCcw :size="10" class="inline mr-1" />
                {{ $t('executionHistory.replay') }}
              </button>
              <button
                v-if="execution.status === 'running'"
                @click.stop="handleStop(execution)"
                class="text-xs px-2 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded transition-colors"
                aria-label="Stop"
              >
                <Square :size="10" class="inline mr-1" />
                {{ $t('executionHistory.stop') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="px-4 py-3 border-t border-gray-700 flex items-center justify-between">
          <button
            @click="currentPage = Math.max(1, currentPage - 1)"
            :disabled="currentPage === 1"
            class="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded transition-colors"
            aria-label="Previous page"
          >
            {{ $t('executionHistory.previous') }}
          </button>
          <span class="text-sm text-gray-400">
            {{ $t('executionHistory.page', { current: currentPage, total: totalPages }) }}
          </span>
          <button
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 rounded transition-colors"
            aria-label="Next page"
          >
            {{ $t('executionHistory.next') }}
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  History,
  X,
  Loader,
  CheckCircle,
  XCircle,
  Clock,
  Pause,
  RotateCcw,
  Square
} from 'lucide-vue-next'
import ExecutionHistoryFilters from './ExecutionHistoryFilters.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  workflowId: {
    type: String,
    required: true
  },
  workflowName: {
    type: String,
    default: ''
  },
  executions: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'select', 'replay', 'stop'])
const { t } = useI18n()

// State
const currentFilters = ref({
  search: '',
  statuses: [],
  timePreset: 'all',
  startDate: '',
  endDate: ''
})
const currentPage = ref(1)
const pageSize = 20
const selectedExecutionId = ref(null)

// Computed
const filteredExecutions = computed(() => {
  let result = [...props.executions]

  // Filter by search
  if (currentFilters.value.search) {
    const query = currentFilters.value.search.toLowerCase()
    result = result.filter(e =>
      e.id.toLowerCase().includes(query) ||
      (e.error && e.error.toLowerCase().includes(query))
    )
  }

  // Filter by status
  if (currentFilters.value.statuses.length > 0) {
    result = result.filter(e =>
      currentFilters.value.statuses.includes(e.status)
    )
  }

  // Filter by date range
  if (currentFilters.value.dateRange?.start) {
    const start = new Date(currentFilters.value.dateRange.start)
    result = result.filter(e => new Date(e.startedAt) >= start)
  }
  if (currentFilters.value.dateRange?.end) {
    const end = new Date(currentFilters.value.dateRange.end)
    result = result.filter(e => new Date(e.startedAt) <= end)
  }

  // Sort by date (newest first)
  result.sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt))

  return result
})

const paginatedExecutions = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredExecutions.value.slice(start, start + pageSize)
})

const totalPages = computed(() =>
  Math.ceil(filteredExecutions.value.length / pageSize)
)

// Methods
function handleFilterChange(filters) {
  currentFilters.value = filters
  currentPage.value = 1 // Reset to first page on filter change
}

function handleSelectExecution(execution) {
  selectedExecutionId.value = execution.id
  emit('select', execution)
}

function handleReplay(execution) {
  emit('replay', execution)
}

function handleStop(execution) {
  emit('stop', execution)
}

function getStatusIcon(status) {
  const icons = {
    success: CheckCircle,
    failed: XCircle,
    running: Loader,
    pending: Clock,
    paused: Pause
  }
  return icons[status] || Clock
}

function getStatusColor(status) {
  const colors = {
    success: 'text-green-400',
    failed: 'text-red-400',
    running: 'text-blue-400',
    pending: 'text-purple-400',
    paused: 'text-yellow-400'
  }
  return colors[status] || 'text-gray-400'
}

function formatTime(timestamp) {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString()
}

function formatDuration(ms) {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

function capitalize(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

// Reset page when panel opens
watch(() => props.isOpen, (open) => {
  if (open) {
    currentPage.value = 1
  }
})
</script>
