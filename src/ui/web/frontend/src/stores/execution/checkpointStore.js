/**
 * Checkpoint Store
 *
 * S-Grade: Human checkpoint management for execution control.
 * Single responsibility: checkpoint state and actions.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as executionAPI from '@/api/executions'
import { telemetry } from '@/services/telemetry'

export const useCheckpointStore = defineStore('checkpoint', () => {
  // ========== State ==========
  const humanCheckpoint = ref(null) // { checkpointId, currentIndex, totalItems, itemPreview }
  const bypassedCheckpoints = ref([]) // checkpoint IDs that have been bypassed
  const loading = ref(false)
  const error = ref(null)

  // ========== Getters ==========
  const hasActiveCheckpoint = computed(() => humanCheckpoint.value !== null)

  const checkpointProgress = computed(() => {
    if (!humanCheckpoint.value) return null
    return {
      current: humanCheckpoint.value.currentIndex,
      total: humanCheckpoint.value.totalItems,
      preview: humanCheckpoint.value.itemPreview
    }
  })

  // ========== Actions ==========

  /**
   * Set human checkpoint state when execution hits a checkpoint
   */
  function setHumanCheckpoint(checkpointData) {
    humanCheckpoint.value = {
      checkpointId: checkpointData.checkpointId,
      currentIndex: checkpointData.currentIndex || 1,
      totalItems: checkpointData.totalItems || 1,
      itemPreview: checkpointData.itemPreview || null
    }
  }

  /**
   * Continue execution from human checkpoint (process next item)
   */
  async function continueFromCheckpoint(executionId) {
    if (!executionId || !humanCheckpoint.value) return false

    loading.value = true
    error.value = null

    try {
      const result = await executionAPI.continueFromCheckpoint(executionId)
      if (result.ok) {
        telemetry.track('execution.checkpoint_continue', {
          execution_id: executionId,
          checkpointId: humanCheckpoint.value?.checkpointId
        })
        humanCheckpoint.value = null
      }
      return result.ok
    } catch (err) {
      error.value = err.userMessage || err.message
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Bypass checkpoint and run all remaining items without stopping
   * @param {string} executionId - Execution ID
   * @param {string} scope - 'this_run' | 'this_version'
   */
  async function bypassCheckpoint(executionId, scope = 'this_run') {
    if (!executionId || !humanCheckpoint.value) return false

    loading.value = true
    error.value = null

    try {
      const checkpointId = humanCheckpoint.value?.checkpointId
      const result = await executionAPI.bypassCheckpoint(executionId, checkpointId, scope)
      if (result.ok) {
        telemetry.track('execution.checkpoint_bypass', {
          execution_id: executionId,
          checkpointId: checkpointId,
          scope
        })
        if (checkpointId) {
          bypassedCheckpoints.value.push(checkpointId)
        }
        humanCheckpoint.value = null
      }
      return result.ok
    } catch (err) {
      error.value = err.userMessage || err.message
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Check if a checkpoint is bypassed
   */
  function isCheckpointBypassed(checkpointId) {
    return bypassedCheckpoints.value.includes(checkpointId)
  }

  /**
   * Clear checkpoint state
   */
  function clearCheckpoint() {
    humanCheckpoint.value = null
  }

  /**
   * Clear bypassed checkpoints (for new execution)
   */
  function clearBypassedCheckpoints() {
    bypassedCheckpoints.value = []
  }

  /**
   * Reset all state
   */
  function reset() {
    humanCheckpoint.value = null
    bypassedCheckpoints.value = []
    loading.value = false
    error.value = null
  }

  return {
    // State
    humanCheckpoint,
    bypassedCheckpoints,
    loading,
    error,

    // Getters
    hasActiveCheckpoint,
    checkpointProgress,

    // Actions
    setHumanCheckpoint,
    continueFromCheckpoint,
    bypassCheckpoint,
    isCheckpointBypassed,
    clearCheckpoint,
    clearBypassedCheckpoints,
    reset
  }
})
