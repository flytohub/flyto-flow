<template>
  <div>
  <!-- Debug Panels -->
  <EvidencePanel
    :is-open="activeDebugPanel === 'evidence'"
    :execution-id="executionId"
    :step-id="selectedStepId"
    @close="$emit('close')"
  />

  <LineagePanel
    :is-open="activeDebugPanel === 'lineage'"
    :execution-id="executionId"
    :step-id="selectedStepId"
    @close="$emit('close')"
    @node-selected="$emit('lineage-node-select', $event)"
  />

  <ReplayPanel
    :is-open="activeDebugPanel === 'replay'"
    :execution-id="executionId"
    :steps="workflowSteps"
    @close="$emit('close')"
    @replay-started="$emit('replay-started', $event)"
  />

  <TestPanel
    :is-open="activeDebugPanel === 'tests'"
    :workflow-id="workflowId"
    @close="$emit('close')"
    @tests-completed="$emit('tests-completed', $event)"
  />

  <VersionPanel
    :is-open="activeDebugPanel === 'versions'"
    :workflow-id="workflowId"
    :modules="usedModules"
    @close="$emit('close')"
    @lock-changed="$emit('version-lock-changed', $event)"
  />

  <!-- Execution History Panel -->
  <ExecutionHistoryPanel
    :is-open="activeDebugPanel === 'history'"
    :workflow-id="workflowId"
    :workflow-name="workflowName"
    :executions="executions"
    :is-loading="isLoadingHistory"
    @close="$emit('close')"
    @select="$emit('select-execution', $event)"
    @replay="$emit('replay-execution', $event)"
    @stop="$emit('stop-execution', $event)"
  />
  </div>
</template>

<script setup>
import { defineAsyncComponent } from 'vue'

const EvidencePanel = defineAsyncComponent(() => import('../debug/EvidencePanel.vue'))
const LineagePanel = defineAsyncComponent(() => import('../debug/LineagePanel.vue'))
const ReplayPanel = defineAsyncComponent(() => import('../debug/ReplayPanel.vue'))
const TestPanel = defineAsyncComponent(() => import('../debug/TestPanel.vue'))
const VersionPanel = defineAsyncComponent(() => import('../debug/VersionPanel.vue'))
const ExecutionHistoryPanel = defineAsyncComponent(() => import('../debug/ExecutionHistoryPanel.vue'))

defineProps({
  activeDebugPanel: { type: String, default: null },
  executionId: { type: String, default: null },
  selectedStepId: { type: String, default: null },
  workflowId: { type: String, default: null },
  workflowName: { type: String, default: '' },
  workflowSteps: { type: Array, default: () => [] },
  usedModules: { type: Array, default: () => [] },
  executions: { type: Array, default: () => [] },
  isLoadingHistory: { type: Boolean, default: false }
})

defineEmits([
  'close',
  'lineage-node-select',
  'replay-started',
  'tests-completed',
  'version-lock-changed',
  'select-execution',
  'replay-execution',
  'stop-execution'
])
</script>
