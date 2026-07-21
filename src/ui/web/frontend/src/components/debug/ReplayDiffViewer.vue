<template>
  <div class="flex flex-col h-full bg-[#0a0a0f]">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700/30 bg-gray-900/50">
      <div class="flex items-center gap-4">
        <!-- Diff Summary -->
        <div class="flex items-center gap-2">
          <div
            :class="[
              'px-2.5 py-1 rounded-lg text-xs font-bold',
              differenceCount > 0
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
            ]"
          >
            {{ differenceCount }} {{ differenceCount === 1 ? $t('debug.replay.difference') : $t('debug.replay.differences') }}
          </div>
        </div>

        <!-- Filter Toggle -->
        <label class="flex items-center gap-2 cursor-pointer group">
          <input
            v-model="showOnlyDiff"
            type="checkbox"
            class="w-4 h-4 rounded border-gray-600 bg-gray-800 text-emerald-600 focus:ring-emerald-500 focus:ring-offset-0 cursor-pointer"
          />
          <span class="text-xs text-gray-400 group-hover:text-gray-300 transition-colors">{{ $t('debug.replay.showOnlyDiff') }}</span>
        </label>
      </div>

      <!-- Legend -->
      <div class="flex items-center gap-3 text-xs">
        <div class="flex items-center gap-1.5">
          <div class="w-2.5 h-2.5 rounded bg-red-500/50" />
          <span class="text-gray-400">{{ $t('debug.replay.removed') }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-2.5 h-2.5 rounded bg-emerald-500/50" />
          <span class="text-gray-400">{{ $t('debug.replay.added') }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <div class="w-2.5 h-2.5 rounded bg-amber-500/50" />
          <span class="text-gray-400">{{ $t('debug.replay.changed') }}</span>
        </div>
      </div>
    </div>

    <!-- Split View -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Original Side -->
      <div class="flex-1 border-r border-gray-700/30 flex flex-col overflow-hidden">
        <!-- Side Header -->
        <div class="sticky top-0 bg-gray-800/80 backdrop-blur px-4 py-2.5 border-b border-gray-700/30 z-10">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full bg-red-400" />
              <h4 class="text-sm font-semibold text-gray-300">{{ $t('debug.replay.originalExecution') }}</h4>
            </div>
            <span class="text-xs text-gray-500 tabular-nums">{{ originalStepCount }} {{ $t('debug.replay.steps') }}</span>
          </div>
        </div>

        <!-- Steps List -->
        <div class="flex-1 overflow-auto" ref="originalScrollRef" @scroll="handleOriginalScroll">
          <div class="divide-y divide-gray-700/20">
            <div
              v-for="step in displayedOriginalSteps"
              :key="`original-${step.id}`"
              class="hover:bg-gray-800/30 transition-colors"
            >
              <div
                @click="selectStep(step, 'original')"
                :class="[
                  'p-4 cursor-pointer transition-all',
                  getStepClass(step, 'original')
                ]"
              >
                <!-- Step Header -->
                <div class="flex items-center gap-3 mb-2">
                  <div
                    :class="[
                      'w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold',
                      step.status === 'failed'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : 'bg-gray-700/50 text-gray-400 border border-gray-600/30'
                    ]"
                  >
                    {{ getStepIndex(step.id, 'original') + 1 }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <span class="text-sm font-medium text-white truncate block">{{ step.name || step.id }}</span>
                    <code class="text-xs text-gray-500 font-mono">{{ step.moduleId }}</code>
                  </div>

                  <!-- Diff Badge -->
                  <div v-if="getDiffType(step.id)" class="flex-shrink-0">
                    <span
                      :class="[
                        'px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded',
                        getDiffType(step.id) === 'status_changed' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                        getDiffType(step.id) === 'result_changed' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                        getDiffType(step.id) === 'removed' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      ]"
                    >
                      {{ getDiffLabel(step.id) }}
                    </span>
                  </div>
                </div>

                <!-- Output Preview -->
                <div class="ml-10">
                  <pre class="text-xs text-gray-400 font-mono overflow-hidden whitespace-pre-wrap line-clamp-2">{{ formatOutput(step.output) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Replay Side -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Side Header -->
        <div class="sticky top-0 bg-gray-800/80 backdrop-blur px-4 py-2.5 border-b border-gray-700/30 z-10">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full bg-emerald-400" />
              <h4 class="text-sm font-semibold text-gray-300">{{ $t('debug.replay.replayResult') }}</h4>
            </div>
            <span class="text-xs text-gray-500 tabular-nums">{{ replayStepCount }} {{ $t('debug.replay.steps') }}</span>
          </div>
        </div>

        <!-- Steps List -->
        <div class="flex-1 overflow-auto" ref="replayScrollRef" @scroll="handleReplayScroll">
          <div class="divide-y divide-gray-700/20">
            <div
              v-for="step in displayedReplaySteps"
              :key="`replay-${step.id}`"
              class="hover:bg-gray-800/30 transition-colors"
            >
              <div
                @click="selectStep(step, 'replay')"
                :class="[
                  'p-4 cursor-pointer transition-all',
                  getStepClass(step, 'replay')
                ]"
              >
                <!-- Step Header -->
                <div class="flex items-center gap-3 mb-2">
                  <div
                    :class="[
                      'w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold',
                      step.status === 'failed'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : 'bg-gray-700/50 text-gray-400 border border-gray-600/30'
                    ]"
                  >
                    {{ getStepIndex(step.id, 'replay') + 1 }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <span class="text-sm font-medium text-white truncate block">{{ step.name || step.id }}</span>
                    <code class="text-xs text-gray-500 font-mono">{{ step.moduleId }}</code>
                  </div>

                  <!-- Diff Badge -->
                  <div v-if="getDiffType(step.id)" class="flex-shrink-0">
                    <span
                      :class="[
                        'px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded',
                        getDiffType(step.id) === 'status_changed' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                        getDiffType(step.id) === 'result_changed' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                        getDiffType(step.id) === 'added' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                        'bg-red-500/20 text-red-400 border border-red-500/30'
                      ]"
                    >
                      {{ getDiffLabel(step.id) }}
                    </span>
                  </div>
                </div>

                <!-- Output Preview -->
                <div class="ml-10">
                  <pre class="text-xs text-gray-400 font-mono overflow-hidden whitespace-pre-wrap line-clamp-2">{{ formatOutput(step.output) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Diff Detail Panel -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-4"
    >
      <div
        v-if="selectedDiff"
        class="border-t border-gray-700/50 bg-gray-900/80 backdrop-blur max-h-[40%] overflow-auto"
      >
        <div class="p-4">
          <!-- Header -->
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <div
                :class="[
                  'w-8 h-8 rounded-lg flex items-center justify-center',
                  selectedDiff.type === 'status_changed' ? 'bg-amber-500/20 border border-amber-500/30' :
                  selectedDiff.type === 'result_changed' ? 'bg-blue-500/20 border border-blue-500/30' :
                  selectedDiff.type === 'added' ? 'bg-emerald-500/20 border border-emerald-500/30' :
                  'bg-red-500/20 border border-red-500/30'
                ]"
              >
                <component
                  :is="getDiffIcon(selectedDiff.type)"
                  :size="16"
                  :class="[
                    selectedDiff.type === 'status_changed' ? 'text-amber-400' :
                    selectedDiff.type === 'result_changed' ? 'text-blue-400' :
                    selectedDiff.type === 'added' ? 'text-emerald-400' :
                    'text-red-400'
                  ]"
                />
              </div>
              <div>
                <h4 class="text-sm font-semibold text-white">{{ selectedDiff.stepId }}</h4>
                <p class="text-xs text-gray-400">{{ getDiffDescription(selectedDiff) }}</p>
              </div>
            </div>
            <button
              @click="selectedDiff = null"
              class="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
              aria-label="Close"
            >
              <X :size="16" />
            </button>
          </div>

          <!-- Diff Content -->
          <div v-if="selectedDiff.type === 'status_changed'" class="grid grid-cols-2 gap-4">
            <div class="p-3 bg-red-950/30 rounded-xl border border-red-500/20">
              <p class="text-xs text-gray-400 mb-1">{{ $t('debug.replay.originalStatus') }}</p>
              <p class="text-sm font-medium text-red-300">{{ selectedDiff.originalStatus }}</p>
              <pre v-if="selectedDiff.originalError" class="mt-2 text-xs text-red-300/70 font-mono">{{ selectedDiff.originalError }}</pre>
            </div>
            <div class="p-3 bg-emerald-950/30 rounded-xl border border-emerald-500/20">
              <p class="text-xs text-gray-400 mb-1">{{ $t('debug.replay.replayStatus') }}</p>
              <p class="text-sm font-medium text-emerald-300">{{ selectedDiff.replayStatus }}</p>
              <pre v-if="selectedDiff.replayError" class="mt-2 text-xs text-emerald-300/70 font-mono">{{ selectedDiff.replayError }}</pre>
            </div>
          </div>

          <div v-else-if="selectedDiff.type === 'result_changed'" class="space-y-3">
            <!-- Field Diffs -->
            <div v-if="selectedDiff.fieldDiffs?.length" class="space-y-2">
              <div
                v-for="(fd, idx) in selectedDiff.fieldDiffs.slice(0, 5)"
                :key="idx"
                class="p-3 bg-gray-800/50 rounded-xl border border-gray-700/30"
              >
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-xs font-mono text-gray-300">{{ fd.field }}</span>
                  <span
                    :class="[
                      'px-1.5 py-0.5 text-[9px] font-bold uppercase rounded',
                      fd.type === 'added' ? 'bg-emerald-500/20 text-emerald-400' :
                      fd.type === 'removed' ? 'bg-red-500/20 text-red-400' :
                      'bg-amber-500/20 text-amber-400'
                    ]"
                  >
                    {{ fd.type }}
                  </span>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div v-if="fd.type !== 'added'">
                    <p class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{{ $t('debug.replay.original') }}</p>
                    <pre class="text-xs text-red-300 font-mono bg-red-950/20 p-2 rounded overflow-auto max-h-24">{{ formatValue(fd.original || fd.value) }}</pre>
                  </div>
                  <div v-if="fd.type !== 'removed'">
                    <p class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{{ $t('debug.replay.replay') }}</p>
                    <pre class="text-xs text-emerald-300 font-mono bg-emerald-950/20 p-2 rounded overflow-auto max-h-24">{{ formatValue(fd.replay || fd.value) }}</pre>
                  </div>
                </div>
              </div>
              <p v-if="selectedDiff.fieldDiffs.length > 5" class="text-xs text-gray-500 text-center">
                {{ $t('debug.replay.moreDifferences', { count: selectedDiff.fieldDiffs.length - 5 }) }}
              </p>
            </div>

            <!-- Full Result Comparison -->
            <div v-else class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{{ $t('debug.replay.originalResult') }}</p>
                <pre class="text-xs text-red-300 font-mono bg-red-950/20 p-3 rounded-xl border border-red-500/20 overflow-auto max-h-40">{{ formatValue(selectedDiff.originalResult) }}</pre>
              </div>
              <div>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{{ $t('debug.replay.replayResult') }}</p>
                <pre class="text-xs text-emerald-300 font-mono bg-emerald-950/20 p-3 rounded-xl border border-emerald-500/20 overflow-auto max-h-40">{{ formatValue(selectedDiff.replayResult) }}</pre>
              </div>
            </div>
          </div>

          <div v-else-if="selectedDiff.type === 'added'" class="p-3 bg-emerald-950/30 rounded-xl border border-emerald-500/20">
            <p class="text-xs text-gray-400 mb-2">{{ $t('debug.replay.stepAddedInReplay') }}</p>
            <pre class="text-xs text-emerald-300 font-mono overflow-auto max-h-32">{{ formatValue(selectedDiff.replayResult) }}</pre>
          </div>

          <div v-else-if="selectedDiff.type === 'removed'" class="p-3 bg-red-950/30 rounded-xl border border-red-500/20">
            <p class="text-xs text-gray-400 mb-2">{{ $t('debug.replay.stepNotExecuted') }}</p>
            <pre class="text-xs text-red-300 font-mono overflow-auto max-h-32">{{ formatValue(selectedDiff.originalResult) }}</pre>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { X, AlertTriangle, Plus, Minus, RefreshCw } from 'lucide-vue-next'

const props = defineProps({
  original: {
    type: Object,
    default: () => ({ steps: [] })
  },
  replay: {
    type: Object,
    default: () => ({ steps: [] })
  },
  differences: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['step-selected'])

const { t } = useI18n()

const showOnlyDiff = ref(false)
const selectedDiff = ref(null)
const syncScroll = ref(true)

const originalScrollRef = ref(null)
const replayScrollRef = ref(null)

// Computed
const differenceCount = computed(() => props.differences?.length || 0)

const originalStepCount = computed(() => props.original?.steps?.length || 0)
const replayStepCount = computed(() => props.replay?.steps?.length || 0)

const diffStepIds = computed(() => {
  return new Set(props.differences?.map(d => d.stepId) || [])
})

const diffMap = computed(() => {
  const map = {}
  for (const diff of (props.differences || [])) {
    map[diff.stepId] = diff
  }
  return map
})

const displayedOriginalSteps = computed(() => {
  const steps = props.original?.steps || []
  if (!showOnlyDiff.value) return steps
  return steps.filter(s => diffStepIds.value.has(s.id))
})

const displayedReplaySteps = computed(() => {
  const steps = props.replay?.steps || []
  if (!showOnlyDiff.value) return steps
  return steps.filter(s => diffStepIds.value.has(s.id))
})

// Methods
function getDiffType(stepId) {
  return diffMap.value[stepId]?.type
}

function getDiffLabel(stepId) {
  const type = getDiffType(stepId)
  if (!type) return ''
  switch (type) {
    case 'status_changed': return t('debug.replay.status')
    case 'result_changed': return t('debug.replay.changed')
    case 'added': return t('debug.replay.added')
    case 'removed': return t('debug.replay.removed')
    default: return type
  }
}

function getDiffIcon(type) {
  switch (type) {
    case 'status_changed': return AlertTriangle
    case 'result_changed': return RefreshCw
    case 'added': return Plus
    case 'removed': return Minus
    default: return RefreshCw
  }
}

function getDiffDescription(diff) {
  switch (diff.type) {
    case 'status_changed':
      return t('debug.replay.statusChangedDesc', { original: diff.originalStatus, replay: diff.replayStatus })
    case 'result_changed':
      return t('debug.replay.outputValuesDiffer')
    case 'added':
      return t('debug.replay.stepAddedInReplay')
    case 'removed':
      return t('debug.replay.stepNotExecuted')
    default:
      return diff.message || t('debug.replay.stepDiffers')
  }
}

function getStepIndex(stepId, side) {
  const steps = side === 'original' ? props.original?.steps : props.replay?.steps
  return (steps || []).findIndex(s => s.id === stepId)
}

function getStepClass(step, side) {
  const diffType = getDiffType(step.id)

  if (!diffType) {
    return ''
  }

  if (side === 'original') {
    if (diffType === 'removed' || diffType === 'result_changed' || diffType === 'status_changed') {
      return 'bg-red-950/20 border-l-2 border-red-500/50'
    }
  } else {
    if (diffType === 'added') {
      return 'bg-emerald-950/20 border-l-2 border-emerald-500/50'
    }
    if (diffType === 'result_changed' || diffType === 'status_changed') {
      return 'bg-emerald-950/20 border-l-2 border-emerald-500/50'
    }
  }

  return ''
}

function selectStep(step, side) {
  const diff = diffMap.value[step.id]
  if (diff) {
    selectedDiff.value = diff
  }
  emit('step-selected', step.id)
}

function formatOutput(output) {
  if (!output) return '-'
  if (typeof output === 'string') {
    return output.length > 150 ? output.substring(0, 150) + '...' : output
  }
  const json = JSON.stringify(output, null, 2)
  return json.length > 150 ? json.substring(0, 150) + '...' : json
}

function formatValue(value) {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'string') return value
  return JSON.stringify(value, null, 2)
}

// Synchronized scrolling
let isScrolling = false

function handleOriginalScroll(e) {
  if (!syncScroll.value || isScrolling) return
  isScrolling = true
  if (replayScrollRef.value) {
    replayScrollRef.value.scrollTop = e.target.scrollTop
  }
  setTimeout(() => { isScrolling = false }, 50)
}

function handleReplayScroll(e) {
  if (!syncScroll.value || isScrolling) return
  isScrolling = true
  if (originalScrollRef.value) {
    originalScrollRef.value.scrollTop = e.target.scrollTop
  }
  setTimeout(() => { isScrolling = false }, 50)
}
</script>
