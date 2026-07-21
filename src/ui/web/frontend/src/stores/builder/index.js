/**
 * Builder Stores Index
 * Barrel export for all builder-related stores
 */

export { useBuilderMetadataStore } from './metadataStore'
export { useBuilderUIStore } from './uiStateStore'
export { useBuilderWorkflowStore } from './workflowStore'
export { useBuilderExecutionStore } from './executionStore'

/**
 * Composable to get all builder stores at once
 * Useful for components that need access to multiple stores
 */
export function useBuilderStores() {
  const { useBuilderMetadataStore } = require('./metadataStore')
  const { useBuilderUIStore } = require('./uiStateStore')
  const { useBuilderWorkflowStore } = require('./workflowStore')
  const { useBuilderExecutionStore } = require('./executionStore')

  return {
    metadata: useBuilderMetadataStore(),
    ui: useBuilderUIStore(),
    workflow: useBuilderWorkflowStore(),
    execution: useBuilderExecutionStore()
  }
}

/**
 * Reset all builder stores
 * Call this when navigating away from the builder
 */
export function resetAllBuilderStores() {
  const { useBuilderMetadataStore } = require('./metadataStore')
  const { useBuilderUIStore } = require('./uiStateStore')
  const { useBuilderWorkflowStore } = require('./workflowStore')
  const { useBuilderExecutionStore } = require('./executionStore')

  useBuilderMetadataStore().resetTemplate()
  useBuilderUIStore().reset()
  useBuilderWorkflowStore().reset()
  useBuilderExecutionStore().reset()
}
