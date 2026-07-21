/**
 * Run Workflow Action
 *
 * S-Grade: Workflow execution action.
 * Single responsibility: Prepare and execute workflow.
 */

import yaml from 'js-yaml'
import { workflowAPI } from '@/api/workflows'
import { templatesAPI } from '@/api/templates'
import { elementsToBackendStepsAsync } from '@/utils/converter'
import { moatTelemetry } from '@/services/moatTelemetry'
import { useToast } from '@/composables/useToast'
import { useI18n } from 'vue-i18n'

function hasInputValues(uiInputValues) {
  return Object.keys(uiInputValues).length > 0
}

function buildInputParams(uiInputValues) {
  return hasInputValues(uiInputValues) ? { ui: uiInputValues } : {}
}

function resolveValue(value, fallback = '') {
  return value?.value ?? value ?? fallback
}

function setExecutionStarted(state, executionId, startPolling, pollingId) {
  state.isExecuting.value = true
  state.currentExecutionId.value = executionId
  if (pollingId === undefined) {
    startPolling()
    return
  }
  startPolling(pollingId)
}

function setExecutionFailed(state) {
  state.isExecuting.value = false
}

function errorMessage(error) {
  return error.response?.data?.detail || error.message || 'Unknown error'
}

function showLowBalanceWarning() {
  const toast = useToast()
  const { t } = useI18n()
  toast.warning(t('wallet.lowBalanceWarning'))
}

async function executeCloudWorkflow({ templateId, templateName, uiInputValues, state, startJobPolling }) {
  const tid = resolveValue(templateId, null)
  if (!tid) {
    return { ok: false, error: 'Save your workflow before running on cloud.' }
  }

  const result = await runOnCloud({
    templateId: tid,
    templateName: resolveValue(templateName),
    uiInputValues,
  })

  if (!result.ok) {
    setExecutionFailed(state)
    return { ok: false, error: result.error }
  }

  setExecutionStarted(state, result.jobId, startJobPolling, result.jobId)
  return { ok: true, executionId: result.jobId }
}

async function executeLockedTemplate({ templateId, uiInputValues, state, startExecutionPolling }) {
  const result = await templatesAPI.executeTemplate(templateId, buildInputParams(uiInputValues))

  if (!result.ok) {
    setExecutionFailed(state)
    return { ok: false, error: result.error || 'Execution failed' }
  }

  const executionId = result.execution_id || result.executionId
  setExecutionStarted(state, executionId, startExecutionPolling)
  if (result.low_balance) {
    showLowBalanceWarning()
  }
  return { ok: true, executionId }
}

function splitElements(elements) {
  return {
    nodes: elements.filter(el => el.id && !el.source && !el.target),
    edges: elements.filter(el => el.source && el.target)
  }
}

function addEdges(workflow, edges) {
  if (edges.length === 0) return
  workflow.edges = edges.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    sourceHandle: e.sourceHandle,
    targetHandle: e.targetHandle,
    type: e.type,
    data: e.data,
    label: e.label
  }))
}

function buildWorkflow({ templateId, templateName, steps, edges, checkpoints }) {
  const workflow = {
    id: templateId || `workflow_${Date.now()}`,
    name: templateName || 'Untitled Workflow',
    version: '1.0.0',
    steps
  }
  addEdges(workflow, edges)
  if (checkpoints && checkpoints.length > 0) {
    workflow.checkpoints = checkpoints
  }
  return workflow
}

function debugStepRange(workflow, debugSelectedNodeIds) {
  const stepIndices = workflow.steps
    .map((step, index) => debugSelectedNodeIds.value.includes(step.id) ? index : -1)
    .filter(index => index >= 0)

  if (stepIndices.length === 0) {
    return {}
  }
  return {
    startStep: Math.min(...stepIndices),
    endStep: Math.max(...stepIndices)
  }
}

function buildRunOptions({ workflow, checkpoints, debugMode, debugSelectedNodeIds, screenshotMode }) {
  const options = {}
  if (debugMode.value && debugSelectedNodeIds.value.length > 0) {
    Object.assign(options, debugStepRange(workflow, debugSelectedNodeIds))
  }
  if (checkpoints && checkpoints.length > 0) {
    options.breakpoints = checkpoints
  }
  if (screenshotMode.value && screenshotMode.value !== 'off') {
    options.screenshotMode = screenshotMode.value
  }
  return options
}

function trackPinnedSteps(templateId, steps) {
  const pinnedSteps = steps.filter(step => step.pinned_output !== undefined)
  if (pinnedSteps.length === 0) return
  moatTelemetry.trackPinSkipExecution(templateId, pinnedSteps.length, steps.length)
}

async function executeLocalWorkflow(context) {
  const {
    elements,
    templateId,
    templateName,
    uiInputValues,
    checkpoints,
    state,
    debugMode,
    debugSelectedNodeIds,
    screenshotMode,
    startExecutionPolling,
  } = context
  const { nodes, edges } = splitElements(elements)
  if (nodes.length === 0) {
    return { ok: false, error: 'NO_STEPS' }
  }

  const steps = await elementsToBackendStepsAsync(elements)
  if (!steps || steps.length === 0) {
    return { ok: false, error: 'NO_VALID_STEPS' }
  }

  trackPinnedSteps(templateId, steps)
  const workflow = buildWorkflow({ templateId, templateName, steps, edges, checkpoints })
  const yamlContent = yaml.dump(workflow, { indent: 2, lineWidth: -1 })
  const options = buildRunOptions({ workflow, checkpoints, debugMode, debugSelectedNodeIds, screenshotMode })
  const result = await workflowAPI.run(yamlContent, buildInputParams(uiInputValues), options)

  if (!result.ok) {
    setExecutionFailed(state)
    return { ok: false, error: result.error || result.message }
  }

  setExecutionStarted(state, result.executionId, startExecutionPolling)
  return { ok: true, executionId: result.executionId }
}

/**
 * Run workflow on a cloud browser worker
 * @param {Object} options
 * @param {string} options.templateId - Template ID
 * @param {string} options.templateName - Template name
 * @param {Object} options.uiInputValues - UI input values
 * @returns {Promise<Object>} { ok, jobId }
 */
export async function runOnCloud({ templateId, templateName, uiInputValues = {} }) {
  try {
    const { post } = await import('@/api/client')
    const result = await post('/devices/cloud/execute', {
      template_id: templateId,
      template_name: templateName || '',
      input_params: buildInputParams(uiInputValues),
    })

    if (result.ok) {
      return { ok: true, jobId: result.jobId || result.job_id }
    }
    return { ok: false, error: result.error || 'Cloud execution failed' }
  } catch (error) {
    return { ok: false, error: errorMessage(error) }
  }
}

/**
 * Create run workflow action
 * @param {Object} state - State refs
 * @param {Object} pollingActions - Polling actions
 * @returns {Object} Run workflow action
 */
export function createRunWorkflowAction(state, pollingActions) {
  const {
    isExecuting,
    currentExecutionId,
    debugMode,
    debugSelectedNodeIds,
    screenshotMode
  } = state
  const { startExecutionPolling, startJobPolling } = pollingActions
  const executionState = { isExecuting, currentExecutionId }

  /**
   * Run workflow
   * @param {Object} options - Execution options
   * @param {Array} options.elements - VueFlow elements
   * @param {string} options.templateId - Template ID
   * @param {string} options.templateName - Template name
   * @param {Object} options.uiInputValues - UI input values keyed by variable_name
   * @param {Array} options.checkpoints - Human checkpoint node IDs
   * @param {boolean} options.isWorkflowLocked - If true, use direct API execution (for locked templates)
   * @returns {Promise<Object>} Execution result
   */
  async function runWorkflow({ elements, templateId, templateName, uiInputValues = {}, checkpoints = [], isWorkflowLocked = false }) {
    try {
      const useJobQueue = import.meta.env.VITE_CLOUD_EXECUTION === 'true'
      if (useJobQueue) {
        return executeCloudWorkflow({
          templateId,
          templateName,
          uiInputValues,
          state: executionState,
          startJobPolling,
        })
      }

      if (isWorkflowLocked && templateId) {
        return executeLockedTemplate({
          templateId,
          uiInputValues,
          state: executionState,
          startExecutionPolling,
        })
      }

      return executeLocalWorkflow({
        elements,
        templateId,
        templateName,
        uiInputValues,
        checkpoints,
        state: executionState,
        debugMode,
        debugSelectedNodeIds,
        screenshotMode,
        startExecutionPolling,
      })
    } catch (error) {
      setExecutionFailed(executionState)
      return { ok: false, error: errorMessage(error) }
    }
  }

  return {
    runWorkflow,
    runOnCloud
  }
}
