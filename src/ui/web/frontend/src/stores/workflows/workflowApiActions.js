/**
 * Workflow API Actions
 *
 * S-Grade: Workflow CRUD operations.
 * Single responsibility: API communication.
 */

import { workflowAPI } from '@/api/workflows'
import i18n from '@/i18n'
import {
  normalizeWorkflowListResponse,
  normalizeWorkflowPayload
} from '@/utils/dataBoundary'

/**
 * Create workflow CRUD action handlers
 * @param {Object} state - State refs
 * @returns {Object} CRUD action functions
 */
export function createWorkflowApiActions(state) {
  const { workflows, currentWorkflow, isLoading, error, enabledCount, totalCount } = state

  /**
   * Fetch workflows list
   */
  async function fetchWorkflows(options = {}) {
    isLoading.value = true
    error.value = null

    try {
      const result = await workflowAPI.list(options)
      const normalized = normalizeWorkflowListResponse(Array.isArray(result) ? { workflows: result } : result)

      enabledCount.value = normalized.enabledCount
      totalCount.value = normalized.totalCount
      if (!normalized.ok) {
        workflows.value = []
        error.value = normalized.error || i18n.global.t('error.failedToLoadWorkflows')
      } else {
        workflows.value = normalized.workflows
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToLoadWorkflows')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch single workflow by ID
   */
  async function fetchWorkflowById(id) {
    isLoading.value = true
    error.value = null

    try {
      const data = await workflowAPI.getById(id)
      currentWorkflow.value = normalizeWorkflowPayload(data)
      return currentWorkflow.value
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToLoadWorkflow')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create workflow
   */
  async function createWorkflow(workflowData) {
    isLoading.value = true
    error.value = null

    try {
      const data = await workflowAPI.create(workflowData)
      const workflow = normalizeWorkflowPayload(data)
      if (workflow) {
        workflows.value.push(workflow)
      }
      currentWorkflow.value = workflow
      return workflow
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToCreateWorkflow')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update workflow
   */
  async function updateWorkflow(id, workflowData) {
    isLoading.value = true
    error.value = null

    try {
      const data = await workflowAPI.update(id, workflowData)
      const workflow = normalizeWorkflowPayload(data)
      const index = workflows.value.findIndex(w => w?.id === id)
      if (index !== -1 && workflow) {
        workflows.value[index] = workflow
      }
      if (currentWorkflow.value?.id === id) {
        currentWorkflow.value = workflow
      }
      return workflow
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUpdateWorkflow')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete workflow
   */
  async function deleteWorkflow(id) {
    isLoading.value = true
    error.value = null

    try {
      await workflowAPI.delete(id)
      workflows.value = workflows.value.filter(w => w?.id !== id)
      if (currentWorkflow.value?.id === id) {
        currentWorkflow.value = null
      }
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToDeleteWorkflow')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Duplicate workflow
   */
  async function duplicateWorkflow(id) {
    isLoading.value = true
    error.value = null

    try {
      const data = await workflowAPI.duplicate(id)
      const workflow = normalizeWorkflowPayload(data)
      if (workflow) {
        workflows.value.push(workflow)
      }
      return workflow
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToDuplicateWorkflow')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Toggle workflow enabled state
   */
  async function toggleWorkflow(id, enabled) {
    isLoading.value = true
    error.value = null

    try {
      const data = await workflowAPI.toggle(id, enabled)
      const workflow = normalizeWorkflowPayload(data)
      const index = workflows.value.findIndex(w => w?.id === id)
      if (index !== -1 && workflow) {
        workflows.value[index] = workflow
      }
      return workflow
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToToggleWorkflow')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    fetchWorkflows,
    fetchWorkflowById,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    duplicateWorkflow,
    toggleWorkflow
  }
}
