<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 relative overflow-hidden">
    <!-- Background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute top-1/2 -left-40 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      <div class="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]"></div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="relative">
        <div class="w-20 h-20 border-4 border-purple-500/20 rounded-full"></div>
        <div class="absolute top-0 left-0 w-20 h-20 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
      </div>
    </div>

    <!-- Error / Not Found -->
    <div v-else-if="error" class="flex flex-col items-center justify-center min-h-screen text-center px-4 relative">
      <div class="w-24 h-24 bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 flex items-center justify-center mb-6">
        <AlertCircle :size="48" class="text-gray-500" />
      </div>
      <h1 class="text-2xl font-bold text-white mb-2">Execution Not Found</h1>
      <p class="text-gray-400 mb-6">{{ error }}</p>
      <button
        @click="router.push('/my-templates')"
        class="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:shadow-lg hover:shadow-purple-500/30 text-white font-medium rounded-xl transition-all"
      >
        Back to Templates
      </button>
    </div>

    <!-- Execution Detail Content -->
    <div v-else class="relative max-w-4xl mx-auto px-4 py-8">
      <!-- Back Navigation -->
      <button
        @click="goBack"
        class="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-6"
      >
        <ArrowLeft :size="18" />
        <span class="text-sm">Back</span>
      </button>

      <!-- Header Card -->
      <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 mb-6">
        <div class="flex items-start justify-between gap-4 mb-4">
          <div class="min-w-0">
            <h1 class="text-xl font-bold text-white mb-1 truncate">
              {{ timelineData?.workflowName || 'Workflow Execution' }}
            </h1>
            <p class="text-sm text-gray-400 font-mono">{{ executionId }}</p>
          </div>
          <span
            class="shrink-0 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide"
            :class="statusClasses"
          >
            {{ displayStatus }}
          </span>
        </div>

        <!-- Stats Row -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div class="bg-gray-900/50 rounded-xl p-3">
            <div class="text-xs text-gray-500 mb-1">Started</div>
            <div class="text-sm text-white font-medium">{{ formattedStartTime }}</div>
          </div>
          <div class="bg-gray-900/50 rounded-xl p-3">
            <div class="text-xs text-gray-500 mb-1">Duration</div>
            <div class="text-sm text-white font-medium">{{ timelineData?.formattedDuration || '-' }}</div>
          </div>
          <div class="bg-gray-900/50 rounded-xl p-3">
            <div class="text-xs text-gray-500 mb-1">Steps</div>
            <div class="text-sm text-white font-medium">
              {{ timelineData?.completedSteps ?? 0 }} / {{ timelineData?.totalSteps ?? 0 }}
            </div>
          </div>
          <div class="bg-gray-900/50 rounded-xl p-3">
            <div class="text-xs text-gray-500 mb-1">Status</div>
            <div class="text-sm font-medium" :style="{ color: timelineData?.statusColor || '#64748b' }">
              {{ displayStatus }}
            </div>
          </div>
        </div>
      </div>

      <!-- Error Section (for failed executions) -->
      <div
        v-if="executionError"
        class="bg-red-500/10 border border-red-500/20 rounded-2xl p-5 mb-6"
      >
        <div class="flex items-center gap-2 mb-3">
          <AlertTriangle :size="18" class="text-red-400" />
          <h2 class="text-base font-semibold text-red-300">Execution Failed</h2>
        </div>
        <p class="text-sm text-red-200/80 mb-2">{{ executionError }}</p>
        <pre
          v-if="executionTraceback"
          class="mt-3 p-3 bg-gray-900/60 rounded-lg text-xs text-gray-400 font-mono overflow-x-auto max-h-48 whitespace-pre-wrap break-words"
        >{{ executionTraceback }}</pre>
      </div>

      <!-- Timeline Section -->
      <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 mb-6">
        <h2 class="text-lg font-semibold text-white mb-4">Execution Timeline</h2>

        <div v-if="timelineLoading" class="flex items-center justify-center py-12">
          <Loader2 :size="24" class="text-purple-500 animate-spin" />
        </div>

        <div v-else-if="timelineEvents.length === 0" class="text-center py-12">
          <Clock :size="40" class="text-gray-600 mx-auto mb-3" />
          <p class="text-gray-500 text-sm">No timeline events</p>
        </div>

        <div v-else class="space-y-0">
          <div
            v-for="(event, index) in timelineEvents"
            :key="`${event.nodeId}-${index}`"
            class="flex gap-3"
          >
            <!-- Timeline Line -->
            <div class="flex flex-col items-center w-5 shrink-0">
              <div
                class="w-3 h-3 rounded-full shrink-0"
                :style="{ backgroundColor: event.statusColor }"
              ></div>
              <div
                v-if="index < timelineEvents.length - 1"
                class="w-0.5 flex-1 min-h-5 bg-gray-700/50 my-1"
              ></div>
            </div>

            <!-- Event Content -->
            <div class="flex-1 pb-4 min-w-0">
              <div class="flex items-center justify-between gap-2 mb-1">
                <span class="text-sm font-medium text-white truncate">
                  {{ event.moduleId || event.nodeId }}
                </span>
                <span class="text-xs text-purple-400 font-medium shrink-0">
                  {{ event.formattedDuration }}
                </span>
              </div>
              <div class="text-xs text-gray-500 capitalize mb-1">{{ event.eventType }}</div>

              <!-- Event Error -->
              <div
                v-if="event.error"
                class="mt-2 p-2.5 bg-red-500/10 border border-red-500/20 rounded-lg"
              >
                <div class="flex items-start gap-1.5">
                  <AlertTriangle :size="13" class="text-red-400 shrink-0 mt-0.5" />
                  <span class="text-xs text-red-300 break-words">{{ event.error }}</span>
                </div>
              </div>

              <!-- Event Output Toggle -->
              <div v-if="event.outputs" class="mt-2">
                <button
                  @click="toggleOutput(event.nodeId, index)"
                  class="flex items-center gap-1.5 px-2 py-1 text-xs text-gray-400 bg-gray-700/30 border border-gray-700/50 rounded hover:bg-gray-700/50 hover:text-gray-300 transition-colors"
                >
                  <Code :size="12" />
                  {{ expandedOutputs[`${event.nodeId}-${index}`] ? 'Hide Output' : 'Show Output' }}
                </button>
                <pre
                  v-if="expandedOutputs[`${event.nodeId}-${index}`]"
                  class="mt-2 p-3 bg-gray-900/60 border border-gray-700/30 rounded-lg text-xs text-gray-400 font-mono overflow-x-auto max-h-48 whitespace-pre-wrap break-words"
                >{{ formatOutput(event.outputs) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap gap-3">
        <!-- Link to Workflow Builder -->
        <button
          v-if="timelineData?.workflowId"
          @click="router.push(`/templates/builder/${timelineData.workflowId}`)"
          class="flex items-center gap-2 px-4 py-2.5 bg-gray-800/50 border border-white/10 rounded-xl text-sm text-gray-300 hover:text-white hover:bg-gray-700/50 transition-all"
        >
          <ExternalLink :size="16" />
          Open in Builder
        </button>

        <!-- Retry Button (failed executions) -->
        <button
          v-if="displayStatus === 'failed' && timelineData?.workflowId"
          @click="retryExecution"
          :disabled="retrying"
          class="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl text-sm text-white font-medium hover:shadow-lg hover:shadow-purple-500/30 transition-all disabled:opacity-50"
        >
          <Loader2 v-if="retrying" :size="16" class="animate-spin" />
          <RotateCcw v-else :size="16" />
          Retry Execution
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Clock,
  Code,
  ExternalLink,
  RotateCcw,
} from 'lucide-vue-next'
import { useExecutionHistory } from '@/composables/useExecutionHistory'
import { getExecutionStatus } from '@/api/executions'

const route = useRoute()
const router = useRouter()

const executionId = computed(() => route.params.id)
const loading = ref(true)
const error = ref(null)
const retrying = ref(false)
const expandedOutputs = ref({})

// Execution data from status API
const executionStatus = ref(null)

// Timeline data from debug API
const {
  timeline: timelineData,
  timelineLoading,
  fetchTimeline,
  formatDuration,
  formatTime,
  normalizeStatus,
  getStatusColor,
} = useExecutionHistory()

const displayStatus = computed(() => {
  if (timelineData.value?.status) return timelineData.value.status
  if (executionStatus.value?.status) return normalizeStatus(executionStatus.value.status)
  return 'unknown'
})

const statusClasses = computed(() => {
  const s = displayStatus.value
  const map = {
    success: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
    failed: 'bg-red-500/20 text-red-400 border border-red-500/30',
    running: 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
    pending: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    cancelled: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
    paused: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
  }
  return map[s] || 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
})

const formattedStartTime = computed(() => {
  const ts = timelineData.value?.startedAt
  if (!ts) return '-'
  try {
    return new Date(ts).toLocaleString()
  } catch {
    return ts
  }
})

const executionError = computed(() => {
  // Check timeline events for errors
  if (executionStatus.value?.error) return executionStatus.value.error
  const events = timelineData.value?.events || []
  const failedEvent = events.find(e => e.error)
  return failedEvent?.error || null
})

const executionTraceback = computed(() => {
  // Check if any event has error category info
  const events = timelineData.value?.events || []
  const failedEvent = events.find(e => e.error && e.errorCategory)
  return failedEvent?.errorCategory || null
})

const timelineEvents = computed(() => {
  return timelineData.value?.events || []
})

function toggleOutput(nodeId, index) {
  const key = `${nodeId}-${index}`
  expandedOutputs.value[key] = !expandedOutputs.value[key]
}

function formatOutput(output) {
  try {
    return JSON.stringify(output, null, 2)
  } catch {
    return String(output)
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/my-templates')
  }
}

async function retryExecution() {
  if (!timelineData.value?.workflowId) return
  retrying.value = true
  try {
    router.push(`/templates/builder/${timelineData.value.workflowId}`)
  } finally {
    retrying.value = false
  }
}

onMounted(async () => {
  const id = executionId.value
  if (!id) {
    error.value = 'No execution ID provided'
    loading.value = false
    return
  }

  try {
    // Fetch both execution status and timeline in parallel
    const [statusResult] = await Promise.allSettled([
      getExecutionStatus(id),
      fetchTimeline(id),
    ])

    if (statusResult.status === 'fulfilled' && statusResult.value?.ok) {
      executionStatus.value = statusResult.value
    }

    // If both failed, show error
    if (!timelineData.value && !executionStatus.value?.ok) {
      error.value = 'Could not load execution details. The execution may have been removed or you may not have access.'
    }
  } catch (err) {
    error.value = err.message || 'Failed to load execution details'
  } finally {
    loading.value = false
  }
})
</script>
