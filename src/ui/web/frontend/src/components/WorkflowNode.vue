<template>
  <component
    :is="nodeComponent"
    v-bind="nodeProps"
    @add-node="emit('add-node', $event)"
    @delete-node="emit('delete-node', $event)"
    @edit-container="emit('edit-container', $event)"
    @retry-node="emit('retry-node', $event)"
    @replace-node="emit('replace-node', $event)"
    @edit-template="emit('edit-template', $event)"
    @save-as-template="emit('save-as-template', $event)"
  />
</template>

<script setup>
import { computed, markRaw } from 'vue'
import { useNodeStyles } from '../composables/useNodeStyles'
import { useModulesStore } from '../stores/modulesStore'
import { resolveNode } from '../config/nodeTypes'
import { getNodeComponent, detectNodeType } from '../config/nodeComponentRegistry'
import { buildNodeProps, createPropsContext } from '../config/nodePropsBuilder'
import { nodeService } from '../services/nodeService'

const modulesStore = useModulesStore()

const {
  getCategoryColor,
  getGradient,
  getCategoryLabel,
  getNodeIcon,
  getNodeLabel,
  getNodeSubtitle,
  getStatusIcon
} = useNodeStyles()

/**
 * Get display label for node — always dynamic from module metadata.
 * Labels reflect current locale and core module changes, never hardcoded.
 */
function getDisplayLabel(moduleId, savedLabel) {
  const metadata = modulesStore.modulesMetadata[moduleId]
  if (!metadata) return savedLabel || moduleId?.split('.').pop() || ''
  return getNodeLabel(moduleId)
}

const props = defineProps({
  id: String,
  data: Object,
  selected: { type: Boolean, default: false },
  isFirst: { type: Boolean, default: false },
  hasLoop: { type: Boolean, default: false },
  edges: { type: Array, default: () => [] },
  hasCheckpoint: { type: Boolean, default: false },
  nodeOutput: { type: [Object, Array, String, Number, Boolean], default: null },
  isPinned: { type: Boolean, default: false },
  compact: { type: Boolean, default: false }
})

const emit = defineEmits(['add-node', 'delete-node', 'edit-container', 'retry-node', 'replace-node', 'edit-template', 'save-as-template'])

// Resolve node configuration (pass modulesStore for nodeType from API)
function normalizeModuleId(value) {
  if (!value) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'object') {
    return value.moduleId || value.id || value.module || ''
  }
  return ''
}

const resolvedModuleId = computed(() => (
  normalizeModuleId(props.data?.module) ||
  normalizeModuleId(props.data?.moduleId)
))
const nodeConfig = computed(() => resolveNode(resolvedModuleId.value, props.data?.params, modulesStore))

// Detect node type using registry (single source of truth)
const detectedType = computed(() => detectNodeType(
  nodeConfig.value.type,
  resolvedModuleId.value,
  props.data
))

// Get component from registry (no more if-else chain)
// Use markRaw to prevent Vue from making the component reactive (performance optimization)
const nodeComponent = computed(() => {
  const component = getNodeComponent(detectedType.value)
  return component ? markRaw(component) : null
})

// Derived state
const isFlowControl = computed(() => nodeConfig.value.isFlowControl)

// Check if node already has a forward edge (main output, not loop/error)
const hasForwardEdge = computed(() => {
  if (!props.edges || !Array.isArray(props.edges)) return false
  return props.edges.some(e => {
    if (e.source !== props.id) return false
    if (e.id?.includes('loop')) return false
    if (e.targetHandle?.includes('loop')) return false
    if (e.sourceHandle?.includes('loop')) return false
    // Error edges don't count — main output should still show "+"
    if (e.sourceHandle === 'source-error') return false
    if (e.id?.startsWith('e_error_')) return false
    return true
  })
})

// Multi-output nodes can always show add button
const isMultiOutput = computed(() => {
  return nodeService.isMultiOutput(resolvedModuleId.value || props.data?.module, modulesStore)
})

const showAddButton = computed(() => {
  if (!nodeConfig.value.showAddButton) return false
  if (hasForwardEdge.value && !isMultiOutput.value) return false
  return true
})

// Build props using registry (no more if-else chain)
const nodeProps = computed(() => {
  const context = createPropsContext({
    id: props.id,
    data: props.data,
    selected: props.selected,
    isFirst: props.isFirst,
    hasLoop: props.hasLoop,
    hasForwardEdge: hasForwardEdge.value,
    showAddButton: showAddButton.value,
    hasCheckpoint: props.hasCheckpoint,
    nodeOutput: props.nodeOutput,
    isPinned: props.isPinned,
    compact: props.compact,
    nodeConfig: nodeConfig.value,
    isFlowControl: isFlowControl.value,
    edges: props.edges,
    styleHelpers: {
      getDisplayLabel,
      getNodeIcon,
      getGradient,
      getNodeSubtitle,
      getStatusIcon,
      getCategoryColor,
      getCategoryLabel
    }
  })

  return buildNodeProps(detectedType.value, context)
})
</script>
