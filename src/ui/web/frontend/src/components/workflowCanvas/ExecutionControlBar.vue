<template>
  <Transition name="control-bar">
    <div v-if="isRunning || isPaused" class="execution-control-bar" :class="{ running: isRunning, paused: isPaused }">
      <!-- Running status indicator -->
      <div v-if="isRunning" class="status-indicator running">
        <Loader2 :size="16" class="status-icon spin" />
        <span class="status-text">{{ $t('debug.execution.running', 'Executing...') }}</span>
      </div>

      <!-- Paused status indicator -->
      <div v-else-if="isPaused" class="status-indicator paused">
        <CirclePause :size="16" class="status-icon" />
        <span class="status-text">{{ $t('debug.checkpoint.pausedAt') }}</span>
      </div>

      <!-- Action buttons -->
      <div class="control-buttons">
        <!-- Pause button (when running and has checkpoints) -->
        <button
          v-if="isRunning && hasCheckpoints"
          class="control-btn pause"
          @click="$emit('pause')"
          :disabled="loading"
          :title="$t('debug.execution.pauseHint', 'Pause execution')"
        >
          <CirclePause :size="16" />
          <span>{{ $t('debug.execution.pause', 'Pause') }}</span>
        </button>

        <!-- Continue (resume to next checkpoint) -->
        <button
          v-if="isPaused"
          class="control-btn primary"
          @click="$emit('resume')"
          :disabled="loading"
          :title="$t('debug.checkpoint.continueHint')"
        >
          <Play :size="16" />
          <span>{{ $t('debug.checkpoint.continue') }}</span>
        </button>

        <!-- Step button (when paused) -->
        <button
          v-if="isPaused"
          class="control-btn step"
          @click="$emit('step')"
          :disabled="loading"
          :title="$t('debug.execution.stepHint', 'Execute next step')"
        >
          <SkipForward :size="16" />
          <span>{{ $t('debug.execution.step', 'Step') }}</span>
        </button>

        <!-- Run to End (ignore all checkpoints) - only show when has checkpoints -->
        <button
          v-if="hasCheckpoints"
          class="control-btn secondary"
          @click="$emit('run-to-end')"
          :disabled="loading"
          :title="$t('debug.checkpoint.runToEndHint')"
        >
          <FastForward :size="16" />
          <span>{{ $t('debug.checkpoint.runToEnd') }}</span>
        </button>

        <!-- Stop button -->
        <button
          class="control-btn danger"
          @click="$emit('stop')"
          :disabled="loading"
          :title="$t('debug.execution.stopHint', 'Stop execution')"
        >
          <Square :size="16" />
          <span>{{ $t('debug.execution.stop', 'Stop') }}</span>
        </button>
      </div>

      <!-- Loading overlay -->
      <div v-if="loading" class="loading-overlay">
        <Loader2 :size="16" class="spin" />
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { CirclePause, Play, FastForward, Loader2, SkipForward, Square } from 'lucide-vue-next'

defineProps({
  isRunning: {
    type: Boolean,
    default: false
  },
  isPaused: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  hasCheckpoints: {
    type: Boolean,
    default: false
  }
})

defineEmits(['pause', 'resume', 'step', 'run-to-end', 'stop'])
</script>

<style scoped>
.execution-control-bar {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 110;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 4px 16px rgba(0, 0, 0, 0.4);
}

.execution-control-bar.running {
  border: 1px solid #8b5cf6;
  box-shadow: 0 8px 32px rgba(139, 92, 246, 0.2), 0 4px 16px rgba(0, 0, 0, 0.4);
}

.execution-control-bar.paused {
  border: 1px solid #f59e0b;
  box-shadow: 0 8px 32px rgba(245, 158, 11, 0.2), 0 4px 16px rgba(0, 0, 0, 0.4);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 16px;
  border-right: 1px solid #334155;
}

.status-indicator.running .status-icon {
  color: #8b5cf6;
}

.status-indicator.running .status-text {
  color: #a78bfa;
}

.status-indicator.paused .status-icon {
  color: #f59e0b;
  animation: pulse 2s infinite;
}

.status-indicator.paused .status-text {
  color: #f59e0b;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.status-text {
  font-size: 13px;
  font-weight: 600;
}

.control-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-btn.primary {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  border-color: #22c55e;
  color: #ffffff;
}

.control-btn.primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  box-shadow: 0 4px 16px rgba(34, 197, 94, 0.3);
  transform: translateY(-1px);
}

.control-btn.secondary {
  background: rgba(71, 85, 105, 0.3);
  border-color: #64748b;
  color: #f1f5f9;
}

.control-btn.secondary:hover:not(:disabled) {
  background: rgba(100, 116, 139, 0.4);
  border-color: #8b5cf6;
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.2);
  transform: translateY(-1px);
}

.control-btn.pause {
  background: rgba(251, 191, 36, 0.15);
  border-color: rgba(251, 191, 36, 0.5);
  color: #fbbf24;
}

.control-btn.pause:hover:not(:disabled) {
  background: rgba(251, 191, 36, 0.25);
  border-color: #f59e0b;
  box-shadow: 0 4px 16px rgba(251, 191, 36, 0.3);
  transform: translateY(-1px);
}

.control-btn.step {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.5);
  color: #60a5fa;
}

.control-btn.step:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.25);
  border-color: #3b82f6;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
}

.control-btn.danger {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.5);
  color: #f87171;
}

.control-btn.danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.25);
  border-color: #ef4444;
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
  transform: translateY(-1px);
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.7);
  border-radius: 12px;
}

.spin {
  animation: spin 1s linear infinite;
  color: #8b5cf6;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Transition animation */
.control-bar-enter-active,
.control-bar-leave-active {
  transition: all 0.3s ease;
}

.control-bar-enter-from,
.control-bar-leave-to {
  opacity: 0;
  transform: translateY(-10px) translateX(10px);
}
</style>
