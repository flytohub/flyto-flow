<template>
  <Transition name="panel-slide">
    <div v-if="isRecording || compiledSteps" class="recording-panel">
      <!-- Header -->
      <div class="panel-header">
        <div class="panel-title">
          <span v-if="isRecording" class="rec-dot"></span>
          <span>{{ isRecording ? 'Recording...' : 'Recorded Steps' }}</span>
        </div>
      </div>

      <!-- Recording active -->
      <div v-if="isRecording" class="panel-body">
        <p class="panel-hint">Interact with the browser — click Stop when done</p>
      </div>

      <!-- Results -->
      <div v-else-if="compiledSteps" class="panel-body">
        <div v-if="hasCompileWarnings" class="panel-warning">
          <div class="warning-title">
            <AlertTriangle :size="14" />
            <span>{{ skippedActionCount }} action{{ skippedActionCount === 1 ? '' : 's' }} skipped</span>
          </div>
          <div
            v-for="warning in visibleWarnings"
            :key="`${warning.code}-${warning.actionIndex ?? warning.action_index}`"
            class="warning-message"
          >
            {{ warning.message }}
          </div>
        </div>
        <div class="panel-actions">
          <div
            v-for="(step, i) in compiledSteps"
            :key="i"
            class="action-item"
          >
            <span class="action-index">{{ i + 1 }}</span>
            <div class="action-detail">
              <span class="action-type">{{ step.module || step.name }}</span>
              <span v-if="step.params?.selector" class="action-target">{{ step.params.selector }}</span>
              <span v-else-if="step.params?.url" class="action-target">{{ step.params.url }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="panel-footer">
        <template v-if="isRecording">
          <button @click="$emit('stop')" class="panel-stop-btn">
            <Square :size="14" />
            Stop & Build Workflow
          </button>
        </template>
        <template v-else-if="compiledSteps">
          <button @click="$emit('apply')" class="panel-apply-btn">
            Apply to Canvas
          </button>
          <button @click="$emit('discard')" class="panel-discard-btn">
            Discard
          </button>
        </template>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { AlertTriangle, Square } from 'lucide-vue-next'
import { useRecordingStore } from '@/stores/recordingStore'

const recordingStore = useRecordingStore()
const { isRecording, compiledSteps, recordingSummary, compileWarnings, hasCompileWarnings } = storeToRefs(recordingStore)
const skippedActionCount = computed(() => {
  return recordingSummary.value?.skippedActionCount ||
    recordingSummary.value?.skipped_action_count ||
    compileWarnings.value.length
})
const visibleWarnings = computed(() => compileWarnings.value.slice(0, 3))

defineEmits(['stop', 'apply', 'discard'])
</script>

<style scoped>
.recording-panel {
  position: fixed;
  right: 20px;
  top: 80px;
  width: 320px;
  max-height: 480px;
  background: #0f172a;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 20px rgba(239, 68, 68, 0.1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

.rec-dot {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  animation: rec-blink 1s ease-in-out infinite;
}

@keyframes rec-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  max-height: 320px;
}

.panel-hint {
  padding: 24px 16px;
  text-align: center;
  font-size: 12px;
  color: #475569;
}

.panel-actions {
  padding: 8px 0;
}

.panel-warning {
  margin: 10px 12px 4px;
  padding: 10px;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.32);
  border-radius: 8px;
}

.warning-title {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #fbbf24;
  font-size: 12px;
  font-weight: 600;
}

.warning-message {
  margin-top: 6px;
  color: #cbd5e1;
  font-size: 11px;
  line-height: 1.4;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
}

.action-item:hover {
  background: rgba(71, 85, 105, 0.2);
}

.action-index {
  width: 20px;
  font-size: 10px;
  color: #475569;
  text-align: right;
  flex-shrink: 0;
}

.action-detail {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.action-type {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}

.action-target {
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.panel-footer {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.panel-stop-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.1));
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 8px;
  color: #f87171;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.panel-stop-btn:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(239, 68, 68, 0.2));
}

.panel-apply-btn {
  flex: 1;
  padding: 8px;
  background: linear-gradient(135deg, #8B5CF6, #7C3AED);
  border: 1px solid rgba(139, 92, 246, 0.5);
  border-radius: 8px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.panel-apply-btn:hover {
  background: linear-gradient(135deg, #9F7AEA, #8B5CF6);
}

.panel-discard-btn {
  padding: 8px 12px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
}

.panel-discard-btn:hover {
  background: rgba(71, 85, 105, 0.5);
}

/* Transition */
.panel-slide-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.panel-slide-leave-active {
  transition: all 0.2s ease-in;
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  opacity: 0;
  transform: translateX(20px) scale(0.95);
}
</style>
