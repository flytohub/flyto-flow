<template>
  <Teleport to="body">
    <Transition name="slide-panel">
      <div
        v-if="isOpen"
        class="fixed inset-y-0 right-0 w-[480px] bg-gray-800 border-l border-gray-700 shadow-2xl z-[1050] flex flex-col"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div class="flex items-center gap-2">
            <Camera :size="18" class="text-blue-400" />
            <h3 class="text-sm font-medium text-white">{{ $t('debug.evidence.title', 'Step Evidence') }}</h3>
          </div>
          <button
            @click="$emit('close')"
            class="p-1 text-gray-400 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X :size="18" />
          </button>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="flex-1 flex items-center justify-center">
          <Loader :size="24" class="text-blue-400 animate-spin" />
        </div>

        <!-- Error -->
        <div v-else-if="error" class="flex-1 flex items-center justify-center text-red-400">
          <div class="text-center px-4">
            <AlertCircle :size="48" class="mx-auto mb-3 opacity-50" />
            <p class="text-sm">{{ error }}</p>
            <button @click="loadData" class="mt-3 text-xs text-blue-400 hover:underline" aria-label="Retry">
              {{ $t('common.retry', 'Retry') }}
            </button>
          </div>
        </div>

        <!-- Step List -->
        <div v-else-if="evidences.length" class="flex-1 flex flex-col overflow-hidden">
          <!-- Step Selector -->
          <div class="p-3 border-b border-gray-700 bg-gray-800/50">
            <AppSelect
              v-model="selectedStepId"
              :placeholder="$t('debug.evidence.selectStep', 'Select a step...')"
              :options="evidences.map(ev => ({ value: ev.stepId, label: ev.stepId + ' - ' + ev.moduleId }))"
            />
          </div>

          <!-- Selected Evidence Content -->
          <div v-if="currentEvidence" class="flex-1 overflow-y-auto">
            <!-- Step Info -->
            <div class="p-4 border-b border-gray-700">
              <div class="flex items-center gap-2 mb-3">
                <component :is="getStatusIcon(currentEvidence.status)" :size="18" :class="getStatusColor(currentEvidence.status)" />
                <span class="text-white font-medium">{{ currentEvidence.stepId }}</span>
                <span class="text-gray-500 text-xs">{{ currentEvidence.moduleId }}</span>
              </div>

              <div class="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p class="text-gray-500 text-xs mb-0.5">{{ $t('debug.evidence.duration', 'Duration') }}</p>
                  <p class="text-white">{{ formatDuration(currentEvidence.durationMs) }}</p>
                </div>
                <div>
                  <p class="text-gray-500 text-xs mb-0.5">{{ $t('debug.evidence.timestamp', 'Time') }}</p>
                  <p class="text-white">{{ formatTime(currentEvidence.timestamp) }}</p>
                </div>
              </div>
            </div>

            <!-- Tab Navigation -->
            <div class="flex border-b border-gray-700">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                class="flex items-center gap-2 px-4 py-2 text-sm transition-colors"
                :class="activeTab === tab.id ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-white'"
                :aria-label="tab.label"
              >
                <component :is="tab.icon" :size="16" />
                {{ tab.label }}
              </button>
            </div>

            <!-- Screenshot Tab -->
            <div v-if="activeTab === 'screenshot'" class="p-4">
              <div v-if="currentEvidence.screenshotPath" class="space-y-3">
                <div class="relative bg-gray-900 rounded-lg overflow-hidden">
                  <img
                    :src="getScreenshotUrl(currentEvidence)"
                    :alt="$t('alt.stepScreenshot')"
                    class="w-full h-auto cursor-pointer"
                    @click="openFullscreen"
                  />
                  <button
                    @click="openFullscreen"
                    class="absolute top-2 right-2 p-2 bg-black/50 rounded-lg text-white hover:bg-black/70 transition-colors"
                    aria-label="Fullscreen"
                  >
                    <Maximize2 :size="16" />
                  </button>
                </div>
                <p class="text-xs text-gray-500">{{ $t('debug.evidence.clickToEnlarge', 'Click to enlarge') }}</p>
              </div>
              <div v-else class="flex flex-col items-center justify-center py-12 text-gray-500">
                <ImageOff :size="48" class="mb-3 opacity-50" />
                <p>{{ $t('debug.evidence.noScreenshot', 'No screenshot available') }}</p>
                <p class="text-xs mt-1">{{ $t('debug.evidence.browserOnly', 'Screenshots are captured for browser modules only') }}</p>
              </div>
            </div>

            <!-- Context Diff Tab -->
            <div v-if="activeTab === 'context'" class="p-4">
              <!-- Loading State -->
              <div v-if="isLoadingDetail" class="flex items-center justify-center py-12">
                <Loader :size="24" class="text-blue-400 animate-spin" />
              </div>

              <!-- Context Data -->
              <div v-else-if="currentEvidence.contextBefore !== undefined || currentEvidence.contextAfter !== undefined" class="space-y-4">
                <!-- Before -->
                <div>
                  <div class="flex items-center gap-2 mb-2">
                    <ArrowLeft :size="14" class="text-yellow-400" />
                    <span class="text-sm font-medium text-gray-300">{{ $t('debug.evidence.contextBefore', 'Before') }}</span>
                  </div>
                  <div class="bg-gray-900 rounded-lg p-3 max-h-48 overflow-auto">
                    <pre class="text-xs text-gray-300 whitespace-pre-wrap">{{ formatJson(currentEvidence.contextBefore) }}</pre>
                  </div>
                </div>

                <!-- Arrow -->
                <div class="flex justify-center">
                  <ArrowDown :size="20" class="text-gray-600" />
                </div>

                <!-- After -->
                <div>
                  <div class="flex items-center gap-2 mb-2">
                    <ArrowRight :size="14" class="text-green-400" />
                    <span class="text-sm font-medium text-gray-300">{{ $t('debug.evidence.contextAfter', 'After') }}</span>
                  </div>
                  <div class="bg-gray-900 rounded-lg p-3 max-h-48 overflow-auto">
                    <pre class="text-xs text-gray-300 whitespace-pre-wrap">{{ formatJson(currentEvidence.contextAfter) }}</pre>
                  </div>
                </div>
              </div>

              <!-- No Context Data -->
              <div v-else class="flex flex-col items-center justify-center py-12 text-gray-500">
                <ArrowRight :size="48" class="mb-3 opacity-50" />
                <p>{{ $t('debug.evidence.noContext', 'No context data available') }}</p>
              </div>
            </div>

            <!-- Output Tab -->
            <div v-if="activeTab === 'output'" class="p-4">
              <!-- Loading State -->
              <div v-if="isLoadingDetail" class="flex items-center justify-center py-12">
                <Loader :size="24" class="text-blue-400 animate-spin" />
              </div>

              <!-- Output/Result Data -->
              <div v-else-if="stepOutput && Object.keys(stepOutput).length" class="bg-gray-900 rounded-lg p-3">
                <pre class="text-xs text-gray-300 whitespace-pre-wrap">{{ formatJson(stepOutput) }}</pre>
              </div>

              <!-- No Output -->
              <div v-else class="flex flex-col items-center justify-center py-12 text-gray-500">
                <FileOutput :size="48" class="mb-3 opacity-50" />
                <p>{{ $t('debug.evidence.noOutput', 'No output data') }}</p>
              </div>
            </div>
          </div>

          <!-- No Step Selected -->
          <div v-else class="flex-1 flex items-center justify-center text-gray-400">
            <div class="text-center">
              <Camera :size="48" class="mx-auto mb-3 opacity-50" />
              <p>{{ $t('debug.evidence.selectStep', 'Select a step to view evidence') }}</p>
            </div>
          </div>
        </div>

        <!-- No Execution ID -->
        <div v-else-if="!executionId" class="flex-1 flex items-center justify-center text-gray-400">
          <div class="text-center px-4">
            <Play :size="48" class="mx-auto mb-3 opacity-50" />
            <p class="font-medium">{{ $t('debug.evidence.runWorkflowFirst', 'Run workflow first') }}</p>
            <p class="text-xs mt-2 text-gray-500">{{ $t('debug.evidence.runFirstHint', 'Execute the workflow to capture step evidence') }}</p>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="flex-1 flex items-center justify-center text-gray-400">
          <div class="text-center px-4">
            <Camera :size="48" class="mx-auto mb-3 opacity-50" />
            <p>{{ $t('debug.evidence.noEvidence', 'No evidence available') }}</p>
            <p class="text-xs mt-2">{{ $t('debug.evidence.runFirst', 'Run the workflow to capture evidence') }}</p>
          </div>
        </div>

        <!-- Fullscreen Modal -->
        <Teleport to="body">
          <div
            v-if="fullscreenOpen && currentEvidence?.screenshotPath"
            class="fixed inset-0 z-[1100] bg-black/90 flex items-center justify-center"
            @click="fullscreenOpen = false"
          >
            <img
              :src="getScreenshotUrl(currentEvidence)"
              :alt="$t('alt.screenshot')"
              class="max-w-[95vw] max-h-[95vh] object-contain"
            />
            <button
              class="absolute top-4 right-4 p-2 text-white hover:text-gray-300"
              @click="fullscreenOpen = false"
              aria-label="Close"
            >
              <X :size="24" />
            </button>
          </div>
        </Teleport>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppSelect from '@/components/common/AppSelect.vue'
import {
  Camera,
  X,
  Loader,
  CheckCircle,
  XCircle,
  Circle,
  Maximize2,
  ImageOff,
  ArrowLeft,
  ArrowRight,
  ArrowDown,
  FileOutput,
  AlertCircle,
  Play
} from 'lucide-vue-next'
import { useEvidence } from '@/composables/debug/useEvidence'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  executionId: {
    type: String,
    default: ''
  },
  stepId: {
    type: String,
    default: ''
  }
})

defineEmits(['close'])
const { t } = useI18n()

// Use the composable
const {
  evidences,
  isLoading,
  error,
  loadEvidences,
  loadStepEvidence,
  getScreenshotUrl: getScreenshotUrlFn,
  reset
} = useEvidence()

const activeTab = ref('screenshot')
const fullscreenOpen = ref(false)
const selectedStepId = ref('')
const stepDetail = ref(null)
const isLoadingDetail = ref(false)

const tabs = computed(() => [
  { id: 'screenshot', label: t('debugTab.screenshot'), icon: Camera },
  { id: 'context', label: t('debugTab.context'), icon: ArrowRight },
  { id: 'output', label: t('debugTab.output'), icon: FileOutput }
])

// Current evidence - use detailed data if available
const currentEvidence = computed(() => {
  if (!selectedStepId.value) return null
  // Prefer detailed step data (has context_before/after)
  if (stepDetail.value && stepDetail.value.stepId === selectedStepId.value) {
    return stepDetail.value
  }
  // Fallback to list data
  return evidences.value.find(e => e.stepId === selectedStepId.value) || null
})

// Step output - try 'result' first, then 'output'
const stepOutput = computed(() => {
  if (!currentEvidence.value) return null
  return currentEvidence.value.result || currentEvidence.value.output || null
})

// Watch for panel open to load data
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen && props.executionId) {
    await loadData()
    // Auto-select stepId if provided
    if (props.stepId) {
      selectedStepId.value = props.stepId
    }
  } else if (!isOpen) {
    reset()
    selectedStepId.value = ''
    stepDetail.value = null
  }
}, { immediate: true })

// Watch executionId changes
watch(() => props.executionId, async (newId) => {
  if (props.isOpen && newId) {
    await loadData()
  }
})

// Watch selectedStepId to load full step details
watch(selectedStepId, async (stepId) => {
  if (!stepId || !props.executionId) {
    stepDetail.value = null
    return
  }

  isLoadingDetail.value = true
  try {
    const result = await loadStepEvidence(props.executionId, stepId)
    if (result.ok) {
      stepDetail.value = result.data
    }
  } finally {
    isLoadingDetail.value = false
  }
})

async function loadData() {
  if (!props.executionId) return
  await loadEvidences(props.executionId)
}

function getScreenshotUrl(evidence) {
  return getScreenshotUrlFn(props.executionId, evidence.stepId)
}

function openFullscreen() {
  fullscreenOpen.value = true
}

function getStatusIcon(status) {
  const icons = {
    success: CheckCircle,
    completed: CheckCircle,
    failed: XCircle,
    error: XCircle
  }
  return icons[status] || Circle
}

function getStatusColor(status) {
  const colors = {
    success: 'text-green-400',
    completed: 'text-green-400',
    failed: 'text-red-400',
    error: 'text-red-400'
  }
  return colors[status] || 'text-gray-500'
}

function formatDuration(ms) {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function formatTime(timestamp) {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleTimeString()
}

function formatJson(obj) {
  if (!obj) return '{}'
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}
</script>

<style scoped>
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: transform 0.3s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateX(100%);
}
</style>
