<template>
  <div
    :class="[
      'relative rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden',
      cardStyles.container,
      isFocused ? 'ring-2 ring-violet-500/50 shadow-lg' : 'hover:shadow-md'
    ]"
    @click="$emit('click', step)"
  >
    <!-- Status Indicator Bar -->
    <div
      :class="[
        'absolute top-0 left-0 w-1 h-full rounded-l-xl',
        statusStyles.bar
      ]"
    />

    <!-- Main Content -->
    <div class="relative p-3 pl-4">
      <!-- Header Row -->
      <div class="flex items-center gap-2">
        <!-- Category Icon -->
        <div
          class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
          :style="{ backgroundColor: categoryConfig.bgColor }"
        >
          <component
            :is="getCategoryIcon()"
            :size="14"
            :style="{ color: categoryConfig.color }"
          />
        </div>

        <!-- Step Name -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-white truncate">
            {{ step.name || step.id }}
          </p>
          <p class="text-xs text-gray-500 font-mono truncate">
            {{ step.moduleId }}
          </p>
        </div>

        <!-- Status Badge -->
        <div
          v-if="step.status"
          :class="[
            'px-2 py-0.5 text-[10px] font-bold uppercase rounded flex-shrink-0',
            statusStyles.badge
          ]"
        >
          {{ step.status === 'completed' ? 'OK' : step.status }}
        </div>
      </div>

      <!-- Artifacts Preview -->
      <div v-if="step.artifacts?.length" class="mt-2 flex items-center gap-1.5">
        <FileText :size="12" class="text-gray-500" />
        <span class="text-xs text-gray-500">{{ step.artifacts.length }} artifacts</span>
        <div class="flex -space-x-1">
          <div
            v-for="(_, idx) in step.artifacts.slice(0, 3)"
            :key="idx"
            class="w-4 h-4 rounded bg-gray-700 border border-gray-600"
          />
        </div>
      </div>

      <!-- Error Preview -->
      <div
        v-if="step.status === 'failed' && step.error"
        class="mt-2 px-2 py-1.5 bg-red-950/30 rounded border border-red-500/20"
      >
        <p class="text-xs text-red-400 truncate">{{ step.error }}</p>
      </div>

      <!-- Duration -->
      <div v-if="step.durationMs" class="mt-2 flex items-center gap-1.5 text-xs text-gray-500">
        <Clock :size="12" />
        <span class="tabular-nums">{{ formatDuration(step.durationMs) }}</span>
      </div>
    </div>

    <!-- Focused Expansion -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 max-h-0"
      enter-to-class="opacity-100 max-h-48"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 max-h-48"
      leave-to-class="opacity-0 max-h-0"
    >
      <div v-if="isFocused" class="border-t border-gray-700/30 overflow-hidden">
        <div class="p-3 space-y-2">
          <!-- Inputs -->
          <div v-if="hasInputs" class="text-xs">
            <span class="text-gray-500">Inputs:</span>
            <div class="mt-1 flex flex-wrap gap-1">
              <code
                v-for="key in Object.keys(step.inputs || {}).slice(0, 5)"
                :key="key"
                class="px-1.5 py-0.5 bg-gray-800 text-gray-300 rounded"
              >
                {{ key }}
              </code>
            </div>
          </div>

          <!-- Outputs -->
          <div v-if="hasOutputs" class="text-xs">
            <span class="text-gray-500">Outputs:</span>
            <div class="mt-1 flex flex-wrap gap-1">
              <code
                v-for="key in Object.keys(step.outputs || {}).slice(0, 5)"
                :key="key"
                class="px-1.5 py-0.5 bg-emerald-900/30 text-emerald-400 rounded"
              >
                {{ key }}
              </code>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Eye,
  Calculator,
  Brain,
  Play,
  CheckCircle,
  FileText,
  Clock
} from 'lucide-vue-next'
import { getCategoryConfig } from './StepCategory'

const props = defineProps({
  step: {
    type: Object,
    required: true
  },
  category: {
    type: String,
    default: null
  },
  isFocused: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const stepCategory = computed(() => props.category || props.step.category || 'act')

const categoryConfig = computed(() => getCategoryConfig(stepCategory.value))

const cardStyles = computed(() => {
  const base = 'bg-gray-900/60 border-gray-700/50'
  if (props.step.status === 'failed') {
    return { container: 'bg-red-950/20 border-red-500/30' }
  }
  if (props.isFocused) {
    return { container: 'bg-violet-950/20 border-violet-500/30' }
  }
  return { container: base + ' hover:border-gray-600' }
})

const statusStyles = computed(() => {
  const status = props.step.status
  if (status === 'completed') {
    return {
      bar: 'bg-emerald-500',
      badge: 'bg-emerald-500/20 text-emerald-400'
    }
  }
  if (status === 'failed') {
    return {
      bar: 'bg-red-500',
      badge: 'bg-red-500/20 text-red-400'
    }
  }
  if (status === 'running') {
    return {
      bar: 'bg-blue-500 animate-pulse',
      badge: 'bg-blue-500/20 text-blue-400'
    }
  }
  return {
    bar: 'bg-gray-600',
    badge: 'bg-gray-500/20 text-gray-400'
  }
})

const hasInputs = computed(() => {
  return props.step.inputs && Object.keys(props.step.inputs).length > 0
})

const hasOutputs = computed(() => {
  return props.step.outputs && Object.keys(props.step.outputs).length > 0
})

function getCategoryIcon() {
  const icons = {
    observe: Eye,
    evaluate: Calculator,
    decide: Brain,
    act: Play,
    verify: CheckCircle
  }
  return icons[stepCategory.value] || Play
}

function formatDuration(ms) {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}
</script>
