/**
 * Run Workflow Action
 *
 * S-Grade: Workflow execution action.
 * Single responsibility: Prepare and execute workflow.
 */

import yaml from 'js-yaml'
import { workflowAPI } from '@/api/workflows'
import { elementsToBackendStepsAsync } from '@/utils/converter'

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
  const { startExecutionPolling } = pollingActions
  const executionState = { isExecuting, currentExecutionId }

  /**
   * Run workflow
   * @param {Object} options - Execution options
   * @param {Array} options.elements - VueFlow elements
   * @param {string} options.templateId - Template ID
   * @param {string} options.templateName - Template name
   * @param {Object} options.uiInputValues - UI input values keyed by variable_name
   * @param {Array} options.checkpoints - Human checkpoint node IDs
   * @returns {Promise<Object>} Execution result
   */
  async function runWorkflow({ elements, templateId, templateName, uiInputValues = {}, checkpoints = [] }) {
    try {
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
    runWorkflow
  }
}
