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
        class="fixed top-0 right-0 h-full w-[520px] bg-gradient-to-b from-gray-900 to-gray-950 border-l border-gray-700/50 shadow-2xl z-40 flex flex-col"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-700/50 bg-gradient-to-r from-amber-900/30 to-amber-800/10">
          <div class="flex items-center gap-4">
            <div class="p-2.5 bg-amber-500/20 rounded-xl border border-amber-500/30">
              <FlaskConical :size="22" class="text-amber-400" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ $t('debug.tests.title') }}</h3>
              <p class="text-xs text-gray-400 mt-0.5">
                {{ tests.length }} {{ $t('debug.tests.testsFound') }}
                <span v-if="error" class="text-red-400 ml-2">{{ error }}</span>
              </p>
            </div>
          </div>
          <button
            @click="$emit('close')"
            class="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-200"
            aria-label="Close"
          >
            <X :size="20" />
          </button>
        </div>

        <!-- Summary Bar -->
        <div v-if="hasResults" class="flex items-center gap-6 px-5 py-3.5 border-b border-gray-700/30 bg-gray-800/30">
          <div class="flex items-center gap-2.5">
            <div class="p-1.5 bg-green-500/20 rounded-lg">
              <CheckCircle :size="16" class="text-green-400" />
            </div>
            <span class="text-sm font-medium text-green-400">{{ passedCount }} {{ $t('debug.tests.passed') }}</span>
          </div>
          <div class="flex items-center gap-2.5">
            <div class="p-1.5 bg-red-500/20 rounded-lg">
              <XCircle :size="16" class="text-red-400" />
            </div>
            <span class="text-sm font-medium text-red-400">{{ failedCount }} {{ $t('debug.tests.failed') }}</span>
          </div>
          <div class="flex-1" />
          <div
            class="px-3 py-1.5 rounded-full text-sm font-bold"
            :class="allPassed ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'"
          >
            {{ passRate }}%
          </div>
        </div>

        <!-- Loading -->
        <div v-if="isLoading && !hasTests" class="flex-1 flex flex-col items-center justify-center gap-4">
          <div class="relative">
            <div class="w-16 h-16 rounded-full border-4 border-gray-700"></div>
            <div class="absolute inset-0 w-16 h-16 rounded-full border-4 border-t-amber-400 animate-spin"></div>
          </div>
          <p class="text-gray-400">{{ $t('debug.tests.loading') }}</p>
        </div>

        <!-- Test List -->
        <div v-else-if="hasTests" class="flex-1 overflow-auto">
          <!-- Running Indicator -->
          <div v-if="isRunning" class="px-5 py-3 bg-gradient-to-r from-amber-900/20 to-transparent border-b border-amber-600/20">
            <div class="flex items-center gap-3">
              <div class="relative">
                <div class="w-5 h-5 rounded-full border-2 border-gray-600"></div>
                <div class="absolute inset-0 w-5 h-5 rounded-full border-2 border-t-amber-400 animate-spin"></div>
              </div>
              <span class="text-sm font-medium text-amber-400">{{ $t('debug.tests.running') }}</span>
            </div>
          </div>

          <TestResultList
            :tests="tests"
            :results="testResults"
            :selected-id="selectedTest?.id || selectedTest?.name"
            @select="handleSelectTest"
            @rerun="handleRerunTest"
          />
        </div>

        <!-- Empty State -->
        <div v-else class="flex-1 flex flex-col items-center justify-center text-center px-8">
          <div class="p-6 bg-gray-800/50 rounded-2xl border border-gray-700/50 mb-6">
            <FlaskConical :size="56" class="text-gray-600" />
          </div>
          <h4 class="text-lg font-medium text-white mb-2">{{ $t('debug.tests.noTests') }}</h4>
          <p class="text-sm text-gray-500 mb-6 max-w-xs">
            {{ $t('debug.tests.noTestsHint') }}
          </p>
          <button
            @click="handleLoadTests"
            :disabled="isLoading"
            class="px-6 py-2.5 bg-amber-600 hover:bg-amber-500 disabled:bg-gray-700 text-white text-sm font-medium rounded-xl transition-all duration-200 flex items-center gap-2 shadow-lg shadow-amber-600/20"
            aria-label="Load tests"
          >
            <RefreshCw :size="16" :class="{ 'animate-spin': isLoading }" />
            {{ $t('debug.tests.loadTests') }}
          </button>
        </div>

        <!-- Selected Test Details -->
        <Transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="opacity-0 translate-y-4"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-4"
        >
          <div
            v-if="selectedTest && selectedResult"
            class="border-t border-gray-700/50 bg-gradient-to-b from-gray-800/80 to-gray-900 p-5 max-h-80 overflow-auto"
          >
            <div class="flex items-center justify-between mb-4">
              <h4 class="text-sm font-semibold text-white flex items-center gap-2">
                <component
                  :is="selectedResult.passed ? CheckCircle : XCircle"
                  :size="16"
                  :class="selectedResult.passed ? 'text-green-400' : 'text-red-400'"
                />
                {{ selectedTest.name }}
              </h4>
              <button
                @click="selectedTest = null"
                class="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                aria-label="Close"
              >
                <X :size="14" />
              </button>
            </div>

            <!-- Assertions -->
            <div v-if="selectedResult.assertionDetails?.length" class="space-y-2 mb-4">
              <p class="text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('debug.tests.assertions') }}</p>
              <div class="space-y-1.5">
                <div
                  v-for="(assertion, index) in selectedResult.assertionDetails"
                  :key="index"
                  class="flex items-start gap-2.5 p-2.5 rounded-lg"
                  :class="assertion.passed ? 'bg-green-500/10' : 'bg-red-500/10'"
                >
                  <component
                    :is="assertion.passed ? CheckCircle : XCircle"
                    :size="14"
                    class="mt-0.5 flex-shrink-0"
                    :class="assertion.passed ? 'text-green-400' : 'text-red-400'"
                  />
                  <span class="text-xs text-gray-300">{{ assertion.message || `${assertion.field}: ${assertion.type}` }}</span>
                </div>
              </div>
            </div>

            <!-- Expected vs Actual -->
            <div v-if="!selectedResult.passed && selectedResult.expectedOutputs" class="space-y-3">
              <div>
                <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ $t('debug.tests.expected') }}</p>
                <pre class="p-3 bg-green-900/20 text-green-300 rounded-lg text-xs overflow-auto border border-green-900/30">{{ formatValue(selectedResult.expectedOutputs) }}</pre>
              </div>
              <div>
                <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ $t('debug.tests.actual') }}</p>
                <pre class="p-3 bg-red-900/20 text-red-300 rounded-lg text-xs overflow-auto border border-red-900/30">{{ formatValue(selectedResult.actualOutputs) }}</pre>
              </div>
            </div>

            <!-- Error Message -->
            <div v-if="selectedResult.error" class="mt-4">
              <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ $t('debug.tests.error') }}</p>
              <pre class="p-3 bg-red-900/20 text-red-300 rounded-lg text-xs overflow-auto border border-red-900/30">{{ selectedResult.error }}</pre>
            </div>

            <!-- Duration -->
            <div class="mt-4 flex items-center gap-2 text-xs text-gray-500">
              <Clock :size="12" />
              {{ selectedResult.durationMs || 0 }}ms
            </div>
          </div>
        </Transition>

        <!-- Actions -->
        <div class="px-5 py-4 border-t border-gray-700/50 bg-gray-800/50">
          <div class="flex gap-3">
            <button
              @click="handleRunAll"
              :disabled="isRunning || !hasTests"
              class="flex-1 py-2.5 px-5 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-amber-600/20 disabled:shadow-none"
              aria-label="Run all tests"
            >
              <Play :size="16" />
              {{ $t('debug.tests.runAll') }}
            </button>
            <button
              v-if="failedCount > 0"
              @click="handleRunFailed"
              :disabled="isRunning"
              class="py-2.5 px-5 bg-red-600/20 hover:bg-red-600/30 border border-red-500/50 text-red-400 text-sm font-medium rounded-xl transition-all duration-200 flex items-center gap-2"
            >
              <RefreshCw :size="16" />
              {{ $t('debug.tests.runFailed') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  FlaskConical,
  X,
  CheckCircle,
  XCircle,
  Play,
  RefreshCw,
  Clock
} from 'lucide-vue-next'
import { useWorkflowTests } from '@/composables/debug/useWorkflowTests'
import TestResultList from './TestResultList.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  workflowId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close', 'test-selected', 'tests-completed'])

const { t } = useI18n()

const {
  tests,
  testResults,
  isLoading,
  isRunning,
  error,
  passedCount,
  failedCount,
  passRate,
  hasTests,
  hasResults,
  allPassed,
  loadTests,
  runTests,
  reset
} = useWorkflowTests({
  workflowId: props.workflowId,
  onSuccess: (event) => {
    if (event === 'tests_passed' || event === 'tests_failed') {
      emit('tests-completed', { passed: event === 'tests_passed' })
    }
  }
})

const selectedTest = ref(null)

const selectedResult = computed(() => {
  if (!selectedTest.value) return null
  return testResults.value.find(r =>
    r.testName === selectedTest.value.name ||
    r.testId === selectedTest.value.id
  )
})

// Load tests when panel opens
watch(() => props.isOpen, async (open) => {
  if (open && props.workflowId) {
    await loadTests(props.workflowId)
  }
})

async function handleLoadTests() {
  await loadTests(props.workflowId)
}

async function handleRunAll() {
  selectedTest.value = null
  await runTests(props.workflowId)
}

async function handleRunFailed() {
  const failedNames = testResults.value
    .filter(r => !r.passed)
    .map(r => r.testName)
  await runTests(props.workflowId, failedNames)
}

function handleSelectTest(test) {
  selectedTest.value = test
  emit('test-selected', test)
}

async function handleRerunTest(test) {
  await runTests(props.workflowId, [test.name])
}

function formatValue(value) {
  if (value === undefined) return 'undefined'
  if (value === null) return 'null'
  if (typeof value === 'string') return value
  return JSON.stringify(value, null, 2)
}
</script>
