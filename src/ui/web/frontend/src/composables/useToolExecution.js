/**
 * Tool Execution Composable
 * Handles workflow execution, polling, and status tracking
 */

import { ref } from 'vue'
import { get } from '@/api/client'
import i18n from '@/i18n'
import { DEFAULTS } from '@/config/defaults'

/**
 * Create tool execution handling composable
 * @param {Object} options
 * @param {Function} options.onComplete - Callback on execution complete
 * @param {Function} options.onError - Callback on execution error
 * @returns {Object} Execution methods and state
 */
export function useToolExecution(options = {}) {
  const { onComplete, onError } = options

  // State
  const isExecuting = ref(false)
  const currentStepIndex = ref(-1)
  const executionResult = ref(null)
  const errorMessage = ref(null)

  /**
   * Build workflow YAML object from tool definition
   */
  function buildWorkflow(tool, steps, inputValues) {
    const workflowSteps = steps.map(step => {
      const params = {}
      for (const [paramName, source] of Object.entries(step.params || {})) {
        if (source.from === 'input' && source.key) {
          params[paramName] = `{{ inputs.${source.key} }}`
        } else if (source.from === 'step' && source.stepId) {
          params[paramName] = `{{ steps.${source.stepId}.output.${source.output || 'result'} }}`
        } else if (source.from === 'fixed') {
          params[paramName] = source.value
        }
      }
      return { id: step.id, module: step.module, params }
    })

    return {
      id: `tool_${tool?.id || 'run'}`,
      name: tool?.meta?.name || 'Tool',
      version: 1,
      steps: workflowSteps
    }
  }

  /**
   * Poll execution status until complete or failed
   */
  async function pollExecution(executionId) {
    const maxAttempts = 120
    let attempts = 0

    while (attempts < maxAttempts) {
      attempts++
      await new Promise(r => setTimeout(r, DEFAULTS.TIMING.POLL_RETRY_DELAY))

      try {
        const data = await get(`/executions/${executionId}`)
        if (!data || data.error) continue
        if (!data.ok || !data.execution) continue

        const exec = data.execution

        if (exec.current_step !== undefined) {
          currentStepIndex.value = exec.current_step
        }

        if (exec.status === 'completed') {
          executionResult.value = exec.outputs || exec.result || { result: 'Completed' }
          return executionResult.value
        } else if (exec.status === 'failed') {
          throw new Error(exec.error || 'Execution failed')
        }
      } catch (e) {
        if (e.message !== 'Execution failed') continue
        throw e
      }
    }

    throw new Error(i18n.global.t('error.executionTimeout'))
  }

  /**
   * Execute the tool workflow
   */
  async function execute(tool, steps, inputValues) {
    if (isExecuting.value) return

    isExecuting.value = true
    currentStepIndex.value = 0
    executionResult.value = null
    errorMessage.value = null

    try {
      const workflow = buildWorkflow(tool, steps, inputValues)
      const yaml = await import('js-yaml')
      const yamlContent = yaml.dump(workflow, { indent: 2 })

      const params = { inputs: { ...inputValues } }

      const { workflowAPI } = await import('@/api/workflows')
      const result = await workflowAPI.run(yamlContent, params)

      if (result.ok) {
        const execResult = await pollExecution(result.executionId)
        onComplete?.(execResult)
        return execResult
      } else {
        throw new Error(result.error || result.message || 'Execution failed')
      }
    } catch (e) {
      errorMessage.value = e.message || 'Execution failed'
      onError?.(e)
      throw e
    } finally {
      isExecuting.value = false
      currentStepIndex.value = -1
    }
  }

  /**
   * Reset execution state
   */
  function reset() {
    isExecuting.value = false
    currentStepIndex.value = -1
    executionResult.value = null
    errorMessage.value = null
  }

  return {
    // State
    isExecuting,
    currentStepIndex,
    executionResult,
    errorMessage,
    // Methods
    execute,
    buildWorkflow,
    pollExecution,
    reset
  }
}
