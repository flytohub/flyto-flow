<template>
  <!-- Resume Panel (when execution failed) -->
  <Teleport to="body">
    <div
      v-if="showResumePanel"
      class="resume-panel-overlay"
      @click.self="$emit('dismiss-resume-panel')"
    >
      <div class="resume-panel-container">
        <ResumePanel
          :failure-node="failureInfo?.node"
          :failure-message="failureInfo?.message"
          :checkpoints="checkpoints"
          :recommended="recommendedCheckpoint"
          :loading="controlLoading"
          @resume="$emit('resume-from-checkpoint', $event)"
          @retry="$emit('retry-execution')"
        />
      </div>
    </div>
  </Teleport>

  <!-- Human Checkpoint Overlay -->
  <CheckpointOverlay
    :visible="isPausedAtCheckpoint"
    :current-index="checkpointProgress?.current || 1"
    :total-items="checkpointProgress?.total || 1"
    :item-preview="checkpointProgress?.preview"
    :loading="controlLoading"
    @continue="$emit('continue-from-checkpoint')"
    @bypass="$emit('bypass-checkpoint')"
  />

  <!-- Browser Screencast Panel -->
  <BrowserPanel
    :is-open="showBrowserPanel"
    :execution-id="executionId"
    @close="$emit('update:showBrowserPanel', false)"
    @browser-closed="$emit('browser-closed')"
  />

  <!-- Execution Timeline Panel (triggered via debug toolbar) -->
  <Transition name="slide-up">
    <div v-if="activeDebugPanel === 'timeline' && timelineNodes.length > 0" class="execution-timeline-panel">
      <div class="timeline-panel-header">
        <span class="timeline-title">{{ $t('execution.timeline', 'Execution Timeline') }}</span>
        <button class="timeline-close-btn" @click="$emit('close-debug-panel')">
          <X :size="16" />
        </button>
      </div>
      <ExecutionTimeline
        :nodes="timelineNodes"
        @select="$emit('timeline-node-select', $event)"
      />
    </div>
  </Transition>

  <!-- Settings Panel (Right Slide-out) -->
  <SettingsPanel
    :show="showSettingsPanel"
    v-model:template-name="templateNameLocal"
    v-model:template-id="templateIdLocal"
    v-model:template-description="templateDescriptionLocal"
    :existing-template-id="existingTemplateId"
    v-model:error-handling="errorHandlingLocal"
    v-model:screenshot-mode="screenshotModeLocal"
    :available-workflows="availableWorkflows"
    @close="$emit('update:showSettingsPanel', false)"
    @import="$emit('settings-import')"
    @export="$emit('settings-export')"
  />

  <!-- Debug Panels -->
  <DebugPanelSection
    :active-debug-panel="activeDebugPanel"
    :execution-id="executionId"
    :selected-step-id="selectedStepId"
    :workflow-id="workflowId"
    :workflow-name="workflowName"
    :workflow-steps="workflowSteps"
    :used-modules="usedModules"
    :executions="executionHistory"
    :is-loading-history="isLoadingHistory"
    @close="$emit('close-debug-panel')"
    @lineage-node-select="$emit('lineage-node-select', $event)"
    @replay-started="$emit('replay-started', $event)"
    @tests-completed="$emit('tests-completed', $event)"
    @version-lock-changed="$emit('version-lock-changed', $event)"
    @select-execution="$emit('select-execution', $event)"
    @replay-execution="$emit('replay-execution', $event)"
    @stop-execution="$emit('stop-execution', $event)"
  />

</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import { X } from 'lucide-vue-next'

// Lazy-loaded components
const ResumePanel = defineAsyncComponent(() => import('../execution/ResumePanel.vue'))
const CheckpointOverlay = defineAsyncComponent(() => import('../execution/CheckpointOverlay.vue'))
const BrowserPanel = defineAsyncComponent(() => import('../execution/BrowserPanel.vue'))
const ExecutionTimeline = defineAsyncComponent(() => import('../execution/ExecutionTimeline.vue'))
const SettingsPanel = defineAsyncComponent(() => import('../templateBuilder/SettingsPanel.vue'))
const DebugPanelSection = defineAsyncComponent(() => import('../templateBuilder/DebugPanelSection.vue'))

const props = defineProps({
  // Resume panel
  showResumePanel: { type: Boolean, default: false },
  failureInfo: { type: Object, default: null },
  checkpoints: { type: Array, default: () => [] },
  recommendedCheckpoint: { type: Object, default: null },
  controlLoading: { type: Boolean, default: false },
  // Checkpoint overlay
  isPausedAtCheckpoint: { type: Boolean, default: false },
  checkpointProgress: { type: Object, default: null },
  // Browser panel
  showBrowserPanel: { type: Boolean, default: false },
  executionId: { type: String, default: '' },
  // Timeline
  activeDebugPanel: { type: String, default: null },
  timelineNodes: { type: Array, default: () => [] },
  // Settings panel
  showSettingsPanel: { type: Boolean, default: false },
  templateName: { type: String, default: '' },
  templateId: { type: String, default: '' },
  templateDescription: { type: String, default: '' },
  existingTemplateId: { type: String, default: null },
  errorHandling: { type: Object, default: () => ({}) },
  screenshotMode: { type: String, default: '' },
  availableWorkflows: { type: Array, default: () => [] },
  // Debug panels
  selectedStepId: { type: String, default: null },
  workflowId: { type: String, default: '' },
  workflowName: { type: String, default: '' },
  workflowSteps: { type: Array, default: () => [] },
  usedModules: { type: Array, default: () => [] },
  executionHistory: { type: Array, default: () => [] },
  isLoadingHistory: { type: Boolean, default: false },
})

const emit = defineEmits([
  'dismiss-resume-panel', 'resume-from-checkpoint', 'retry-execution',
  'continue-from-checkpoint', 'bypass-checkpoint',
  'update:showBrowserPanel', 'browser-closed',
  'close-debug-panel', 'timeline-node-select',
  'update:showSettingsPanel', 'settings-import', 'settings-export',
  'update:templateName', 'update:templateId', 'update:templateDescription',
  'update:errorHandling', 'update:screenshotMode',
  'lineage-node-select', 'replay-started', 'tests-completed',
  'version-lock-changed', 'select-execution', 'replay-execution', 'stop-execution',
])

// v-model proxies for SettingsPanel
const templateNameLocal = computed({
  get: () => props.templateName,
  set: (v) => emit('update:templateName', v)
})

const templateIdLocal = computed({
  get: () => props.templateId,
  set: (v) => emit('update:templateId', v)
})

const templateDescriptionLocal = computed({
  get: () => props.templateDescription,
  set: (v) => emit('update:templateDescription', v)
})

const errorHandlingLocal = computed({
  get: () => props.errorHandling,
  set: (v) => emit('update:errorHandling', v)
})

const screenshotModeLocal = computed({
  get: () => props.screenshotMode,
  set: (v) => emit('update:screenshotMode', v)
})
</script>

<style scoped>
/* Resume Panel Overlay */
.resume-panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.resume-panel-container {
  background: #1e293b;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  padding: 24px;
  min-width: 400px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

/* Execution Timeline Panel */
.execution-timeline-panel {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  max-width: 800px;
  background: rgba(15, 23, 42, 0.98);
  border: 1px solid #334155;
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.4);
  z-index: 100;
  backdrop-filter: blur(12px);
}

.timeline-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #334155;
}

.timeline-title {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

.timeline-close-btn {
  padding: 4px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.timeline-close-btn:hover {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

/* Slide up animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translate(-50%, 100%);
  opacity: 0;
}
</style>
