<template>
  <div
    :class="[
      'relative rounded-xl border transition-all duration-300',
      isCollapsed
        ? 'bg-gradient-to-r from-violet-950/30 to-purple-900/10 border-violet-500/30'
        : 'bg-gray-900/30 border-gray-700/50'
    ]"
  >
    <!-- Header -->
    <div
      class="flex items-center gap-3 p-3 cursor-pointer select-none"
      @click="toggleCollapse"
    >
      <!-- Loop Icon -->
      <div
        :class="[
          'w-8 h-8 rounded-lg flex items-center justify-center',
          isCollapsed
            ? 'bg-violet-500/20'
            : 'bg-gray-800/50'
        ]"
      >
        <RefreshCw
          :size="16"
          :class="[
            'transition-transform duration-300',
            isCollapsed ? 'text-violet-400' : 'text-gray-400',
            isSpinning ? 'animate-spin' : ''
          ]"
        />
      </div>

      <!-- Loop Info -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <span class="text-sm font-medium text-white">
            {{ loopLabel }}
          </span>
          <!-- Iteration Count Badge -->
          <span
            :class="[
              'px-2 py-0.5 text-xs font-bold rounded-full',
              isCollapsed
                ? 'bg-violet-500/20 text-violet-300 border border-violet-500/30'
                : 'bg-gray-700/50 text-gray-300 border border-gray-600/30'
            ]"
          >
            {{ iterations.length }} {{ iterations.length === 1 ? 'iteration' : 'iterations' }}
          </span>
          <!-- Success Rate -->
          <span
            v-if="successRate !== null"
            :class="[
              'px-2 py-0.5 text-xs rounded-full',
              successRate === 100
                ? 'bg-emerald-500/20 text-emerald-400'
                : successRate > 50
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-red-500/20 text-red-400'
            ]"
          >
            {{ successRate }}% success
          </span>
        </div>
        <p v-if="!isCollapsed" class="text-xs text-gray-500 mt-0.5">
          {{ $t('lineage.loop.clickToCollapse') }}
        </p>
      </div>

      <!-- Collapse Indicator -->
      <ChevronDown
        :size="20"
        :class="[
          'transition-transform duration-200',
          isCollapsed ? 'text-violet-400' : 'text-gray-500 rotate-180'
        ]"
      />
    </div>

    <!-- Collapsed Summary -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 max-h-0"
      enter-to-class="opacity-100 max-h-24"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100 max-h-24"
      leave-to-class="opacity-0 max-h-0"
    >
      <div v-if="isCollapsed" class="px-3 pb-3 overflow-hidden">
        <!-- Mini Timeline -->
        <div class="flex items-center gap-1">
          <div
            v-for="(iter, idx) in iterations.slice(0, 10)"
            :key="idx"
            class="group relative"
          >
            <div
              :class="[
                'w-6 h-6 rounded-md flex items-center justify-center text-xs font-medium transition-all',
                iter.success
                  ? 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'
                  : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
              ]"
              @click.stop="$emit('iteration-click', iter, idx)"
            >
              {{ idx + 1 }}
            </div>
            <!-- Tooltip -->
            <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 rounded text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              Iteration {{ idx + 1 }}: {{ iter.success ? 'Success' : 'Failed' }}
            </div>
          </div>
          <span v-if="iterations.length > 10" class="text-xs text-gray-500 ml-1">
            +{{ iterations.length - 10 }}
          </span>
        </div>

        <!-- Decision Summary -->
        <div v-if="lastDecision" class="mt-2 flex items-center gap-2">
          <span class="text-xs text-gray-500">Final:</span>
          <span
            :class="[
              'px-2 py-0.5 text-xs rounded',
              lastDecision.decision === 'pass' || lastDecision.decision === 'complete'
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-amber-500/20 text-amber-400'
            ]"
          >
            {{ lastDecision.decision }}
          </span>
          <span class="text-xs text-gray-500 truncate">
            {{ lastDecision.reason?.slice(0, 50) }}
          </span>
        </div>
      </div>
    </Transition>

    <!-- Expanded Content -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="!isCollapsed" class="border-t border-gray-700/30">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RefreshCw, ChevronDown } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  loopId: {
    type: String,
    required: true
  },
  loopLabel: {
    type: String,
    default: 'Loop'
  },
  iterations: {
    type: Array,
    default: () => []
  },
  defaultCollapsed: {
    type: Boolean,
    default: false
  },
  isRunning: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle', 'iteration-click'])

const isCollapsed = ref(props.defaultCollapsed)
const isSpinning = ref(props.isRunning)

watch(() => props.isRunning, (running) => {
  isSpinning.value = running
})

const successRate = computed(() => {
  if (props.iterations.length === 0) return null
  const successCount = props.iterations.filter(i => i.success).length
  return Math.round((successCount / props.iterations.length) * 100)
})

const lastDecision = computed(() => {
  if (props.iterations.length === 0) return null
  const lastIter = props.iterations[props.iterations.length - 1]
  return lastIter?.decision || null
})

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
  emit('toggle', isCollapsed.value)
}
</script>
