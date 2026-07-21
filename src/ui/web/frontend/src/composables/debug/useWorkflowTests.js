/**
 * useWorkflowTests Composable
 * Manages workflow test execution and results
 */

import { ref, computed, onUnmounted } from 'vue'
import { testingAPI } from '@/api/testing'

export function useWorkflowTests(options = {}) {
  const { workflowId, onError, onSuccess, pollInterval = 1000 } = options

  // State
  const tests = ref([])
  const testResults = ref([])
  const report = ref(null)
  const snapshots = ref([])
  const runningTestId = ref(null)
  const selectedTest = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  let pollTimer = null
  let isMounted = true

  // Computed
  const isRunning = computed(() => runningTestId.value !== null)

  const passedCount = computed(() =>
    testResults.value.filter(r => r.passed).length
  )

  const failedCount = computed(() =>
    testResults.value.filter(r => !r.passed).length
  )

  const totalCount = computed(() => testResults.value.length)

  const passRate = computed(() => {
    if (testResults.value.length === 0) return 0
    return Math.round((passedCount.value / testResults.value.length) * 100)
  })

  const hasTests = computed(() => tests.value.length > 0)

  const hasResults = computed(() => testResults.value.length > 0)

  const allPassed = computed(() =>
    hasResults.value && failedCount.value === 0
  )

  // Actions
  async function loadTests(wfId) {
    const id = wfId || workflowId
    if (!id) return { ok: false, error: 'No workflow ID' }

    isLoading.value = true
    error.value = null

    try {
      const data = await testingAPI.loadTests(id)
      tests.value = data.tests || []
      return { ok: true, data: tests.value }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to load tests'
      onError?.(err)
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function runTests(wfId, testNames = []) {
    const id = wfId || workflowId
    if (!id) return { ok: false, error: 'No workflow ID' }

    isLoading.value = true
    error.value = null
    testResults.value = []

    try {
      const data = await testingAPI.runTests(id, testNames)
      if (data.ok || data.testRunId) {
        runningTestId.value = data.testRunId
        startPolling(data.testRunId)
        return { ok: true, testRunId: data.testRunId }
      }
      throw new Error(data.error || 'Failed to start tests')
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to run tests'
      onError?.(err)
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function runTestsByTags(wfId, tags) {
    const id = wfId || workflowId
    if (!id) return { ok: false, error: 'No workflow ID' }

    isLoading.value = true
    error.value = null
    testResults.value = []

    try {
      const data = await testingAPI.runTestsByTags(id, tags)
      if (data.ok || data.testRunId) {
        runningTestId.value = data.testRunId
        startPolling(data.testRunId)
        return { ok: true, testRunId: data.testRunId }
      }
      throw new Error(data.error || 'Failed to start tests')
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to run tests by tags'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function loadReport(wfId) {
    const id = wfId || workflowId
    if (!id) return { ok: false, error: 'No workflow ID' }

    try {
      const data = await testingAPI.getTestReport(id)
      report.value = data
      return { ok: true, data }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  async function loadSnapshots(wfId) {
    const id = wfId || workflowId
    if (!id) return { ok: false, error: 'No workflow ID' }

    try {
      const data = await testingAPI.listSnapshots(id)
      snapshots.value = data.snapshots || []
      return { ok: true, data: snapshots.value }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  async function updateSnapshot(wfId, snapshotName, newData) {
    const id = wfId || workflowId
    if (!id) return { ok: false, error: 'No workflow ID' }

    isLoading.value = true
    try {
      const data = await testingAPI.updateSnapshot(id, snapshotName, newData)
      onSuccess?.('snapshot_updated')
      await loadSnapshots(id)
      return { ok: true, data }
    } catch (err) {
      error.value = err.message || err.userMessage || 'Failed to update snapshot'
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function deleteSnapshot(wfId, snapshotName) {
    const id = wfId || workflowId
    if (!id) return { ok: false, error: 'No workflow ID' }

    try {
      await testingAPI.deleteSnapshot(id, snapshotName)
      onSuccess?.('snapshot_deleted')
      await loadSnapshots(id)
      return { ok: true }
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }

  function selectTest(test) {
    selectedTest.value = test
  }

  function startPolling(testRunId) {
    stopPolling()
    pollTimer = setInterval(async () => {
      if (!isMounted) {
        stopPolling()
        return
      }
      try {
        const result = await testingAPI.getTestResult(testRunId)
        // Backend returns status: 'completed' | 'running' | 'pending' | 'failed'
        if (result.status === 'completed' || result.status === 'failed') {
          testResults.value = result.results || []
          runningTestId.value = null
          stopPolling()
          onSuccess?.(result.allPassed ? 'tests_passed' : 'tests_failed')
        }
      } catch (e) {
        // Continue polling
      }
    }, pollInterval)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function reset() {
    stopPolling()
    testResults.value = []
    runningTestId.value = null
    selectedTest.value = null
    error.value = null
  }

  onUnmounted(() => {
    isMounted = false
    stopPolling()
  })

  return {
    // State
    tests,
    testResults,
    report,
    snapshots,
    selectedTest,
    isLoading,
    error,

    // Computed
    isRunning,
    passedCount,
    failedCount,
    totalCount,
    passRate,
    hasTests,
    hasResults,
    allPassed,

    // Actions
    loadTests,
    runTests,
    runTestsByTags,
    loadReport,
    loadSnapshots,
    updateSnapshot,
    deleteSnapshot,
    selectTest,
    reset
  }
}

export default useWorkflowTests
