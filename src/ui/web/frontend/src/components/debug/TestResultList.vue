<template>
  <div class="divide-y divide-gray-700/30">
    <!-- Test Items -->
    <div
      v-for="test in sortedTests"
      :key="test.id || test.name"
      @click="handleClick(test)"
      class="group px-5 py-4 hover:bg-white/5 cursor-pointer transition-all duration-200"
      :class="{
        'bg-white/5 border-l-2 border-l-amber-500': isSelected(test),
        'border-l-2 border-l-transparent': !isSelected(test)
      }"
    >
      <div class="flex items-center gap-4">
        <!-- Status Icon -->
        <div class="flex-shrink-0">
          <template v-if="getResult(test)">
            <div
              v-if="getResult(test).passed"
              class="p-2 bg-green-500/20 rounded-lg"
            >
              <CheckCircle :size="18" class="text-green-400" />
            </div>
            <div
              v-else
              class="p-2 bg-red-500/20 rounded-lg"
            >
              <XCircle :size="18" class="text-red-400" />
            </div>
          </template>
          <div v-else class="p-2 bg-gray-700/50 rounded-lg">
            <Circle :size="18" class="text-gray-500" />
          </div>
        </div>

        <!-- Test Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-sm font-medium text-white truncate group-hover:text-amber-200 transition-colors">
              {{ test.name }}
            </span>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <span
              v-for="tag in test.tags"
              :key="tag"
              class="px-2 py-0.5 text-xs bg-gray-700/70 text-gray-400 rounded-md border border-gray-600/50"
            >
              {{ tag }}
            </span>
            <p v-if="test.description && !test.tags?.length" class="text-xs text-gray-500 truncate">
              {{ test.description }}
            </p>
          </div>
        </div>

        <!-- Duration & Actions -->
        <div class="flex items-center gap-3 flex-shrink-0">
          <span
            v-if="getResult(test)?.durationMs"
            class="px-2.5 py-1 text-xs font-mono bg-gray-700/50 text-gray-400 rounded-md"
          >
            {{ getResult(test).durationMs }}ms
          </span>
          <button
            @click.stop="handleRerun(test)"
            class="p-2 text-gray-500 hover:text-amber-400 hover:bg-amber-500/10 rounded-lg transition-all duration-200 opacity-0 group-hover:opacity-100"
            :title="$t('debug.tests.rerun')"
          >
            <RotateCcw :size="16" />
          </button>
        </div>
      </div>

      <!-- Assertions Preview (when selected) -->
      <Transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 max-h-0"
        enter-to-class="opacity-100 max-h-40"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 max-h-40"
        leave-to-class="opacity-0 max-h-0"
      >
        <div
          v-if="isSelected(test) && getResult(test)?.assertionDetails?.length"
          class="mt-3 ml-14 overflow-hidden"
        >
          <div class="p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              {{ $t('debug.tests.assertions') }}
            </p>
            <div class="space-y-1.5">
              <div
                v-for="(assertion, index) in getResult(test).assertionDetails.slice(0, 5)"
                :key="index"
                class="flex items-center gap-2 text-xs"
              >
                <component
                  :is="assertion.passed ? CheckCircle : XCircle"
                  :size="12"
                  :class="assertion.passed ? 'text-green-400' : 'text-red-400'"
                />
                <span class="text-gray-400 truncate">{{ assertion.message || `${assertion.field}: ${assertion.type}` }}</span>
              </div>
              <p
                v-if="getResult(test).assertionDetails.length > 5"
                class="text-xs text-gray-500 mt-2 pl-5"
              >
                +{{ getResult(test).assertionDetails.length - 5 }} {{ $t('debug.tests.moreAssertions') }}
              </p>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Empty State -->
    <div
      v-if="tests.length === 0"
      class="px-5 py-12 text-center"
    >
      <div class="p-4 bg-gray-800/50 rounded-xl inline-block mb-4">
        <FlaskConical :size="32" class="text-gray-600" />
      </div>
      <p class="text-gray-500 text-sm">{{ $t('debug.tests.noTestsInList') }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  CheckCircle,
  XCircle,
  Circle,
  RotateCcw,
  FlaskConical
} from 'lucide-vue-next'

const props = defineProps({
  tests: {
    type: Array,
    default: () => []
  },
  results: {
    type: Array,
    default: () => []
  },
  selectedId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['select', 'rerun'])

const { t } = useI18n()

// Create a map for quick result lookup
const resultMap = computed(() => {
  const map = new Map()
  props.results.forEach(r => {
    map.set(r.testName, r)
    if (r.testId) {
      map.set(r.testId, r)
    }
  })
  return map
})

// Sort tests: failed first, then passed, then not run
const sortedTests = computed(() => {
  return [...props.tests].sort((a, b) => {
    const resultA = getResult(a)
    const resultB = getResult(b)

    // No result = lowest priority
    if (!resultA && !resultB) return 0
    if (!resultA) return 1
    if (!resultB) return -1

    // Failed first
    if (!resultA.passed && resultB.passed) return -1
    if (resultA.passed && !resultB.passed) return 1

    return 0
  })
})

function getResult(test) {
  return resultMap.value.get(test.name) || resultMap.value.get(test.id) || null
}

function isSelected(test) {
  return props.selectedId === test.id || props.selectedId === test.name
}

function handleClick(test) {
  emit('select', test)
}

function handleRerun(test) {
  emit('rerun', test)
}
</script>
