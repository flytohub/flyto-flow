<template>
  <div class="resume-panel">
    <!-- Failure Info -->
    <div v-if="failureNode" class="failure-info">
      <AlertCircle :size="20" class="icon-error" aria-hidden="true" />
      <div class="failure-details">
        <div class="failure-node">{{ failedAtLabel }}: {{ failureNode }}</div>
        <div v-if="failureMessage" class="failure-message">{{ failureMessage }}</div>
      </div>
    </div>

    <!-- Auto-suggest Banner (when recommended checkpoint exists) -->
    <div v-if="recommended && checkpoints.length > 0" class="auto-suggest-banner">
      <div class="suggest-icon">
        <Zap :size="18" />
      </div>
      <div class="suggest-content">
        <div class="suggest-title">{{ $t('execution.resume.autoSuggest', 'Smart Recovery Available') }}</div>
        <div class="suggest-description">
          {{ $t('execution.resume.autoSuggestDesc', 'Resume from the recommended checkpoint to skip {steps} completed steps.', { steps: completedStepsCount }) }}
        </div>
        <div v-if="timeSaved" class="time-saved">
          <Clock :size="12" />
          <span>{{ $t('execution.resume.timeSaved', 'Est. time saved: {time}', { time: formatTimeSaved(timeSaved) }) }}</span>
        </div>
      </div>
      <button class="quick-resume-btn" @click="handleQuickResume" :disabled="loading" aria-label="Quick resume">
        <Play :size="14" />
        <span>{{ $t('execution.resume.quickResume', 'Quick Resume') }}</span>
      </button>
    </div>

    <!-- Checkpoint Selection -->
    <div v-if="checkpoints.length > 0" class="checkpoint-section">
      <div class="section-header">
        <div class="section-title">{{ resumeOptionsLabel }}</div>
        <div v-if="totalSteps" class="steps-info">
          {{ completedStepsCount }} / {{ totalSteps }} {{ $t('execution.resume.stepsCompleted', 'steps completed') }}
        </div>
      </div>
      <CheckpointList
        :checkpoints="checkpoints"
        :recommended="recommended"
        v-model="selectedCheckpoint"
      />
    </div>

    <!-- Actions -->
    <div class="resume-actions">
      <button
        @click="handleResume"
        class="btn btn-primary"
        :disabled="!selectedCheckpoint || loading"
        aria-label="Resume from checkpoint"
      >
        <RotateCcw :size="16" aria-hidden="true" />
        <span>{{ resumeFromCheckpointLabel }}</span>
      </button>

      <button
        @click="handleRetryFromStart"
        class="btn btn-secondary"
        :disabled="loading"
        aria-label="Retry from start"
      >
        <RefreshCw :size="16" aria-hidden="true" />
        <span>{{ retryFromStartLabel }}</span>
      </button>
    </div>

    <!-- n8n Comparison Banner -->
    <div class="comparison-hint">
      <Sparkles :size="12" />
      <span>{{ $t('execution.resume.flytoAdvantage', 'Flyto2 advantage: Resume from failure instead of rerunning from scratch') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { AlertCircle, RotateCcw, RefreshCw, Zap, Clock, Play, Sparkles } from 'lucide-vue-next'
import CheckpointList from './CheckpointList.vue'
import { moatTelemetry } from '@/services/moatTelemetry'

const { t } = useI18n()

const props = defineProps({
  failureNode: {
    type: String,
    default: null
  },
  failureMessage: {
    type: String,
    default: null
  },
  checkpoints: {
    type: Array,
    default: () => []
  },
  recommended: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  // New props for enhanced experience
  totalSteps: {
    type: Number,
    default: null
  },
  completedSteps: {
    type: Number,
    default: null
  },
  averageStepDuration: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['resume', 'retry'])

function handleRetryFromStart() {
  // Track user choosing to retry from start despite checkpoints
  moatTelemetry.trackRetryFromStart(null, props.checkpoints.length)
  emit('retry')
}

const selectedCheckpoint = ref(props.recommended)

watch(() => props.recommended, (newVal) => {
  if (newVal && !selectedCheckpoint.value) {
    selectedCheckpoint.value = newVal
  }
})

// Computed values for time-saving display
const completedStepsCount = computed(() => {
  if (props.completedSteps !== null) return props.completedSteps
  // Estimate from checkpoints if not provided
  return props.checkpoints.filter(cp => cp.type === 'node_complete').length
})

const timeSaved = computed(() => {
  if (!props.averageStepDuration || !completedStepsCount.value) return null
  return completedStepsCount.value * props.averageStepDuration
})

const failedAtLabel = computed(() => t('execution.resume.failedAt', 'Failed at'))
const resumeOptionsLabel = computed(() => t('execution.resume.options', 'Resume Options'))
const resumeFromCheckpointLabel = computed(() => t('execution.resume.fromCheckpoint', 'Resume from Checkpoint'))
const retryFromStartLabel = computed(() => t('execution.resume.retryFromStart', 'Retry from Start'))

// Track when panel is shown
onMounted(() => {
  moatTelemetry.trackFailureShow(
    null, // workflow_id would come from parent
    props.failureNode,
    props.checkpoints.length,
    !!props.recommended
  )
})

function handleResume() {
  if (selectedCheckpoint.value) {
    const checkpoint = props.checkpoints.find(cp => cp.id === selectedCheckpoint.value)

    // Track manual checkpoint selection
    moatTelemetry.trackManualCheckpointSelect(
      null, // workflow_id
      selectedCheckpoint.value,
      selectedCheckpoint.value === props.recommended
    )

    // Track time saved if available
    if (timeSaved.value) {
      moatTelemetry.trackTimeSaved(null, timeSaved.value, completedStepsCount.value)
    }

    emit('resume', selectedCheckpoint.value)
  }
}

function handleQuickResume() {
  if (props.recommended) {
    // Track quick resume
    moatTelemetry.trackQuickResume(
      null, // workflow_id
      props.recommended,
      completedStepsCount.value
    )

    // Track time saved
    if (timeSaved.value) {
      moatTelemetry.trackTimeSaved(null, timeSaved.value, completedStepsCount.value)
    }

    emit('resume', props.recommended)
  }
}

function formatTimeSaved(ms) {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${Math.round(ms / 1000)}s`
  return `${Math.round(ms / 60000)}m`
}
</script>

<style scoped>
.resume-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.failure-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
}

.icon-error {
  color: #ef4444;
  flex-shrink: 0;
  margin-top: 2px;
}

.failure-details {
  flex: 1;
  min-width: 0;
}

.failure-node {
  font-size: 14px;
  font-weight: 600;
  color: #fca5a5;
  margin-bottom: 4px;
}

.failure-message {
  font-size: 13px;
  color: #fecaca;
  line-height: 1.4;
  word-break: break-word;
}

.checkpoint-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.resume-actions {
  display: flex;
  gap: 12px;
  padding-top: 8px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(71, 85, 105, 0.5);
}

/* Auto-suggest banner */
.auto-suggest-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 10px;
  animation: suggest-pulse 2s ease-in-out infinite;
}

@keyframes suggest-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.2); }
  50% { box-shadow: 0 0 12px 2px rgba(34, 197, 94, 0.15); }
}

.suggest-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(34, 197, 94, 0.15);
  border-radius: 8px;
  color: #22c55e;
  flex-shrink: 0;
}

.suggest-content {
  flex: 1;
  min-width: 0;
}

.suggest-title {
  font-size: 14px;
  font-weight: 600;
  color: #22c55e;
  margin-bottom: 4px;
}

.suggest-description {
  font-size: 12px;
  color: #a7f3d0;
  line-height: 1.4;
  margin-bottom: 6px;
}

.time-saved {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #86efac;
  font-weight: 500;
}

.quick-resume-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #22c55e;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.quick-resume-btn:hover:not(:disabled) {
  background: #16a34a;
  transform: translateY(-1px);
}

.quick-resume-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Section header */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.steps-info {
  font-size: 11px;
  color: #64748b;
}

/* Comparison hint */
.comparison-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 8px;
  font-size: 11px;
  color: #a78bfa;
}

.comparison-hint svg {
  flex-shrink: 0;
}
</style>
