<template>
  <div class="container mx-auto px-4 py-6">
    <!-- Search & Filters -->
    <div class="bg-gray-800 rounded-xl border border-gray-700 p-4 mb-6">
      <div class="flex flex-col lg:flex-row gap-4">
        <!-- Search -->
        <div class="flex-1">
          <div class="relative">
            <Search :size="18" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <AppInput
              v-model="searchQuery"
              @keydown="e => { if (e.key === 'Enter') handleSearch() }"
              :placeholder="$t('traces.search.placeholder', 'Search by trace ID, workflow name...')"
              class="!pl-10"
            />
          </div>
        </div>

        <!-- Filters -->
        <div class="flex gap-3">
          <AppSelect
            v-model="statusFilter"
            @change="applyFilters"
            :options="[
              { value: '', label: $t('traces.filter.allStatus', 'All Status') },
              { value: 'completed', label: $t('traces.filter.completed', 'Completed') },
              { value: 'failed', label: $t('traces.filter.failed', 'Failed') },
              { value: 'running', label: $t('traces.filter.running', 'Running') }
            ]"
            size="sm"
          />

          <button
            @click="refreshTraces"
            :disabled="traceStore.isLoading"
            class="px-4 py-2.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw :size="16" :class="{ 'animate-spin': traceStore.isLoading }" />
            {{ $t('common.refresh', 'Refresh') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Trace List -->
      <div class="lg:col-span-1 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div class="p-4 border-b border-gray-700">
          <h3 class="text-lg font-semibold text-white flex items-center gap-2">
            <List :size="20" class="text-purple-400" />
            {{ $t('traces.list.title', 'Traces') }}
            <span class="text-sm text-gray-400">({{ traceStore.pagination.total }})</span>
          </h3>
        </div>

        <!-- Loading -->
        <div v-if="traceStore.isLoading" class="p-4 space-y-3">
          <div v-for="i in 5" :key="i" class="h-16 bg-gray-700/50 rounded animate-pulse"></div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!traceStore.hasTraces" class="p-8 text-center text-gray-400">
          <Workflow :size="48" class="mx-auto mb-3 opacity-50" />
          <p>{{ $t('traces.list.empty', 'No traces found') }}</p>
        </div>

        <!-- Trace List -->
        <div v-else class="divide-y divide-gray-700 max-h-[600px] overflow-y-auto">
          <div
            v-for="trace in traceStore.traces"
            :key="trace.traceId"
            @click="selectTrace(trace)"
            class="p-4 cursor-pointer transition-colors"
            :class="[
              selectedTraceId === trace.traceId
                ? 'bg-purple-900/30 border-l-2 border-purple-500'
                : 'hover:bg-gray-700/50'
            ]"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-white font-medium truncate max-w-[180px]">{{ trace.workflowName }}</span>
              <StatusBadge :status="trace.status" />
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400 font-mono text-xs truncate max-w-[120px]">{{ trace.traceId.slice(0, 8) }}...</span>
              <span class="text-gray-500">{{ formatDuration(trace.durationMs) }}</span>
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ formatRelativeTime(trace.startedAt) }}
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="traceStore.pagination.totalPages > 1" class="p-4 border-t border-gray-700 flex items-center justify-center gap-2">
          <button
            @click="goToPage(traceStore.pagination.page - 1)"
            :disabled="traceStore.pagination.page <= 1"
            class="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft :size="18" />
          </button>
          <span class="text-sm text-gray-400">
            {{ traceStore.pagination.page }} / {{ traceStore.pagination.totalPages }}
          </span>
          <button
            @click="goToPage(traceStore.pagination.page + 1)"
            :disabled="traceStore.pagination.page >= traceStore.pagination.totalPages"
            class="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight :size="18" />
          </button>
        </div>
      </div>

      <!-- Trace Detail / Waterfall -->
      <div class="lg:col-span-2 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <div class="p-4 border-b border-gray-700 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-white flex items-center gap-2">
            <GitBranch :size="20" class="text-purple-400" />
            {{ $t('traces.detail.title', 'Trace Detail') }}
          </h3>
          <button
            v-if="traceStore.hasCurrentTrace"
            @click="openInNewTab"
            class="text-sm text-gray-400 hover:text-white flex items-center gap-1"
          >
            <ExternalLink :size="14" />
            {{ $t('traces.detail.openNew', 'Open in new tab') }}
          </button>
        </div>

        <!-- No Selection -->
        <div v-if="!traceStore.hasCurrentTrace && !traceStore.isLoadingTrace" class="p-8 text-center text-gray-400">
          <MousePointerClick :size="48" class="mx-auto mb-3 opacity-50" />
          <p>{{ $t('traces.detail.selectPrompt', 'Select a trace to view details') }}</p>
        </div>

        <!-- Loading -->
        <div v-else-if="traceStore.isLoadingTrace" class="p-8 text-center">
          <Loader2 :size="32" class="mx-auto mb-3 text-purple-400 animate-spin" />
          <p class="text-gray-400">{{ $t('common.loading', 'Loading...') }}</p>
        </div>

        <!-- Trace Content -->
        <div v-else class="p-4">
          <!-- Trace Info -->
          <div class="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p class="text-xs text-gray-500 mb-1">{{ $t('traces.detail.traceId', 'Trace ID') }}</p>
              <p class="text-sm text-white font-mono truncate">{{ traceStore.currentTrace.traceId }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">{{ $t('traces.detail.duration', 'Duration') }}</p>
              <p class="text-sm text-white">{{ formatDuration(traceStore.currentTrace.durationMs) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">{{ $t('traces.detail.spans', 'Spans') }}</p>
              <p class="text-sm text-white">{{ traceStore.spans.length }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">{{ $t('traces.detail.status', 'Status') }}</p>
              <StatusBadge :status="traceStore.currentTrace.status" />
            </div>
          </div>

          <!-- Waterfall View -->
          <div class="border border-gray-700 rounded-lg overflow-hidden">
            <div class="bg-gray-700/30 px-4 py-2 text-sm font-medium text-gray-300">
              {{ $t('traces.waterfall.title', 'Span Timeline') }}
            </div>
            <SpanWaterfall
              :spans="traceStore.spans"
              :timeline-data="traceStore.timelineData"
              :selected-span="traceStore.selectedSpan"
              @select="traceStore.selectSpan"
            />
          </div>

          <!-- Selected Span Detail -->
          <div v-if="traceStore.selectedSpan" class="mt-4 border border-gray-700 rounded-lg overflow-hidden">
            <div class="bg-gray-700/30 px-4 py-2 text-sm font-medium text-gray-300 flex items-center justify-between">
              <span>{{ $t('traces.spanDetail.title', 'Span Details') }}</span>
              <button @click="traceStore.selectSpan(null)" class="text-gray-400 hover:text-white">
                <X :size="16" />
              </button>
            </div>
            <SpanDetailPanel :span="traceStore.selectedSpan" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { MS_PER_MINUTE, MS_PER_HOUR, MS_PER_DAY } from '@/constants/time'
import { useTraceStore } from '@/stores/traceStore'
import {
  Search,
  RefreshCw,
  List,
  Workflow,
  GitBranch,
  ExternalLink,
  MousePointerClick,
  Loader2,
  ChevronLeft,
  ChevronRight,
  X
} from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import StatusBadge from '@/components/traces/StatusBadge.vue'
import SpanWaterfall from '@/components/traces/SpanWaterfall.vue'
import SpanDetailPanel from '@/components/traces/SpanDetailPanel.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import { formatDuration } from '@/utils/format'

const props = defineProps({
  timeRange: {
    type: String,
    default: '7d'
  }
})

const router = useRouter()
const { t } = useI18n()
const traceStore = useTraceStore()

// Local state
const searchQuery = ref('')
const statusFilter = ref('')
const selectedTraceId = ref(null)

// Format helpers
function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  const minutes = Math.floor(diff / MS_PER_MINUTE)
  if (minutes < 1) return t('time.justNow', 'Just now')
  if (diff < MS_PER_HOUR) return t('time.minutesAgo', '{n} min ago', { n: minutes })

  const hours = Math.floor(diff / MS_PER_HOUR)
  if (diff < MS_PER_DAY) return t('time.hoursAgo', '{n}h ago', { n: hours })

  const days = Math.floor(diff / MS_PER_DAY)
  return t('time.daysAgo', '{n}d ago', { n: days })
}

// Actions
async function selectTrace(trace) {
  selectedTraceId.value = trace.traceId
  await traceStore.fetchTrace(trace.traceId)
}

function handleSearch() {
  if (searchQuery.value.trim()) {
    traceStore.searchTraces(searchQuery.value.trim())
  } else {
    traceStore.fetchTraces()
  }
}

function applyFilters() {
  traceStore.setFilters({ status: statusFilter.value || null })
}

function refreshTraces() {
  traceStore.fetchTraces()
}

function goToPage(page) {
  traceStore.setPage(page)
}

function openInNewTab() {
  if (traceStore.currentTrace) {
    router.push(`/observability/traces/${traceStore.currentTrace.traceId}`)
  }
}

// Watch time range changes
watch(() => props.timeRange, () => {
  traceStore.fetchTraces()
})

onMounted(() => {
  traceStore.fetchTraces()
})
</script>
