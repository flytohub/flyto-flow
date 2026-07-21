<template>
  <div class="process-section">
    <div class="process-indicator">
      <ArrowRight :size="24" />
    </div>

    <!-- Run Button -->
    <button
      class="run-button"
      :class="{ running: isExecuting, disabled: !canRun }"
      :disabled="!canRun || isExecuting"
      @click="$emit('execute')"
    >
      <Loader v-if="isExecuting" :size="24" class="spin" />
      <Play v-else :size="24" />
      <span>{{ isExecuting ? $t('simpleToolView.processing') : $t('simpleToolView.start') }}</span>
    </button>

    <!-- Progress (when running) -->
    <div v-if="isExecuting && steps.length > 0" class="progress-mini">
      <div class="progress-bar">
        <div
          class="progress-fill"
          :style="{ width: `${progressPercent}%` }"
        ></div>
      </div>
      <span class="progress-text">
        {{ currentStepLabel || $t('simpleToolView.processing') }}
      </span>
    </div>

    <div class="process-indicator">
      <ArrowRight :size="24" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowRight, Play, Loader } from 'lucide-vue-next'

const props = defineProps({
  isExecuting: {
    type: Boolean,
    default: false
  },
  canRun: {
    type: Boolean,
    default: true
  },
  steps: {
    type: Array,
    default: () => []
  },
  currentStepIndex: {
    type: Number,
    default: -1
  }
})

defineEmits(['execute'])

const progressPercent = computed(() => {
  if (props.steps.length === 0) return 0
  return Math.min(100, ((props.currentStepIndex + 1) / props.steps.length) * 100)
})

const currentStepLabel = computed(() => {
  if (props.currentStepIndex < 0 || props.currentStepIndex >= props.steps.length) return null
  return props.steps[props.currentStepIndex]?.label
})
</script>

<style scoped>
.process-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 24px 0;
}

.process-indicator {
  color: #475569;
}

.run-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 140px;
  height: 140px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
}

.run-button:hover:not(.disabled):not(.running) {
  transform: scale(1.05);
  box-shadow: 0 15px 50px rgba(16, 185, 129, 0.4);
}

.run-button.disabled {
  background: #334155;
  box-shadow: none;
  cursor: not-allowed;
}

.run-button.running {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 10px 40px rgba(59, 130, 246, 0.3);
}

.progress-mini {
  width: 100%;
  max-width: 160px;
}

.progress-bar {
  height: 4px;
  background: #334155;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  transition: width 0.3s;
}

.progress-text {
  display: block;
  text-align: center;
  font-size: 11px;
  color: #64748b;
  margin-top: 6px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 900px) {
  .process-section {
    flex-direction: row !important;
    padding: 16px 0 !important;
  }
  .process-indicator {
    transform: rotate(90deg);
  }
}
</style>
