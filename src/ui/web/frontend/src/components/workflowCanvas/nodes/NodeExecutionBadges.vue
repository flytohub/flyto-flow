<template>
  <!-- Execution loading overlay -->
  <div v-if="executionState === 'running' && !disabled" class="execution-overlay">
    <div class="execution-spinner" :class="{ 'execution-spinner--compact': compact }"></div>
    <span v-if="!compact" class="execution-text">{{ $t('execution.running', 'Running...') }}</span>
  </div>

  <!-- Execution pending indicator -->
  <div v-if="executionState === 'pending'" class="execution-pending-badge" :class="{ 'badge--compact': compact }">
    <Clock :size="compact ? 10 : 14" aria-hidden="true" />
  </div>

  <!-- Execution completed checkmark -->
  <div v-if="executionState === 'completed'" class="execution-completed-badge" :class="{ 'badge--compact': compact }">
    <Check :size="compact ? 12 : 16" aria-hidden="true" />
  </div>

  <!-- Execution duration badge (bottom-right corner, clickable) -->
  <button
    v-if="executionDuration && !compact && (executionState === 'completed' || executionState === 'error')"
    class="duration-corner"
    :class="{ 'has-error': executionState === 'error' }"
    @click.stop="$emit('show-details')"
    :title="$t('debug.nodeDetail', 'View Details')"
  >
    {{ executionDuration }}
  </button>

  <!-- Output summary chip (bottom-left, clickable) -->
  <button
    v-if="outputSummary && !compact && executionState === 'completed'"
    class="output-summary-chip"
    @click.stop="$emit('show-details')"
    :title="outputSummary"
  >
    {{ outputSummaryDisplay }}
  </button>

  <!-- Execution error indicator -->
  <div v-if="executionState === 'error'" class="execution-error-badge" :class="{ 'badge--compact': compact }">
    <AlertTriangle :size="compact ? 10 : 14" aria-hidden="true" />
  </div>

  <!-- Validation indicator (backend-driven) -->
  <div v-if="validationBadge" class="validation-badge" :class="[`validation-${validationBadge.level}`, { 'badge--compact': compact }]">
    <AlertTriangle v-if="validationBadge.level === 'error'" :size="compact ? 10 : 12" aria-hidden="true" />
    <AlertCircle v-else :size="compact ? 10 : 12" aria-hidden="true" />
    <span v-if="!compact">{{ validationBadge.count }}</span>
  </div>

  <!-- Pinned data badge -->
  <PinnedBadge v-if="isPinned" :compact="compact" />

  <!-- Disabled overlay -->
  <div v-if="disabled" class="disabled-overlay" :class="{ 'disabled-overlay--compact': compact }">
    <CircleSlash :size="compact ? 16 : 20" class="disabled-icon" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Check, Clock, AlertTriangle, AlertCircle, CircleSlash } from 'lucide-vue-next'
import PinnedBadge from '../PinnedBadge.vue'

const props = defineProps({
  executionState: { type: String, default: null },
  executionDuration: { type: String, default: null },
  outputSummary: { type: String, default: null },
  isPinned: { type: Boolean, default: false },
  validation: { type: Object, default: null },
  compact: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false }
})

defineEmits(['show-details'])

const outputSummaryDisplay = computed(() => {
  const s = props.outputSummary
  if (!s) return ''
  return s.length > 20 ? s.slice(0, 18) + '...' : s
})

const validationBadge = computed(() => {
  const v = props.validation
  if (!v) return null
  const errors = Number(v.errors || 0)
  const warnings = Number(v.warnings || 0)
  if (errors > 0) return { level: 'error', count: errors }
  if (warnings > 0) return { level: 'warning', count: warnings }
  return null
})
</script>

<style scoped>
.execution-overlay {
  position: absolute;
  inset: 0;
  background: rgba(30, 41, 59, 0.9);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  z-index: 10;
  backdrop-filter: blur(3px);
}

.execution-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid rgba(139, 92, 246, 0.2);
  border-top-color: #8B5CF6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.execution-spinner--compact {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

.execution-text {
  font-size: 11px;
  color: #A78BFA;
  font-weight: 500;
}

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* Pending state badge */
.execution-pending-badge {
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #6B7280 0%, #4B5563 100%);
  border: 2px solid #1F2937;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  z-index: 15;
  animation: pending-pulse 2s ease-in-out infinite;
}

@keyframes pending-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* Completed state badge */
.execution-completed-badge {
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  border: 2px solid #1F2937;
  border-radius: 50%;
  color: white;
  z-index: 15;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.5);
  animation: badge-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* Duration badge */
.duration-corner {
  position: absolute;
  bottom: -6px;
  right: -6px;
  padding: 2px 6px;
  font-size: 9px;
  font-weight: 600;
  color: white;
  font-family: 'JetBrains Mono', monospace;
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  z-index: 20;
  cursor: pointer;
  transition: all 0.15s ease;
}

.duration-corner:hover {
  background: rgba(51, 65, 85, 0.95);
  border-color: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
}

.duration-corner.has-error {
  background: rgba(127, 29, 29, 0.9);
  border-color: rgba(239, 68, 68, 0.4);
  color: #fecaca;
}

.duration-corner.has-error:hover {
  background: rgba(153, 27, 27, 0.95);
}

/* Output summary chip */
.output-summary-chip {
  position: absolute;
  bottom: -6px;
  left: -6px;
  padding: 2px 6px;
  font-size: 9px;
  font-weight: 500;
  color: #86EFAC;
  font-family: 'JetBrains Mono', monospace;
  background: rgba(5, 46, 22, 0.9);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 8px;
  z-index: 20;
  cursor: pointer;
  transition: all 0.15s ease;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.output-summary-chip:hover {
  background: rgba(5, 46, 22, 0.95);
  border-color: rgba(34, 197, 94, 0.5);
  transform: scale(1.05);
}

/* Error state badge */
.execution-error-badge {
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  border: 2px solid #1F2937;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  z-index: 15;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.5);
  animation: error-shake 0.5s ease-in-out;
}

@keyframes error-shake {
  0%, 100% { transform: translateX(-50%) rotate(0deg); }
  25% { transform: translateX(-50%) rotate(-5deg); }
  75% { transform: translateX(-50%) rotate(5deg); }
}

@keyframes badge-pop {
  0% { transform: translateX(-50%) scale(0); opacity: 0; }
  100% { transform: translateX(-50%) scale(1); opacity: 1; }
}

/* Validation badge */
.validation-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  border: 2px solid #0f172a;
  z-index: 15;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
}

.validation-error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: #fff;
}

.validation-warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #fff;
}

/* Compact mode badge adjustments */
.execution-pending-badge.badge--compact,
.execution-completed-badge.badge--compact,
.execution-error-badge.badge--compact {
  top: -4px;
}

.badge--compact {
  padding: 2px 4px;
}

.execution-pending-badge.badge--compact,
.execution-error-badge.badge--compact {
  width: 18px;
  height: 18px;
}

.execution-completed-badge.badge--compact {
  padding: 2px 4px;
  border-radius: 8px;
}

.validation-badge.badge--compact {
  top: -4px;
  right: -4px;
  padding: 2px 4px;
}

/* Disabled state */
.disabled-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 12;
  pointer-events: none;
}

.disabled-icon {
  color: #F97316;
  opacity: 0.8;
  filter: drop-shadow(0 0 4px rgba(249, 115, 22, 0.5));
}

.disabled-overlay::after {
  content: 'DISABLED';
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  padding: 2px 8px;
  background: linear-gradient(135deg, #F97316 0%, #EA580C 100%);
  border: 2px solid #1F2937;
  border-radius: 8px;
  font-size: 9px;
  font-weight: 700;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  z-index: 20;
}

.disabled-overlay--compact::after {
  font-size: 7px;
  padding: 1px 4px;
  top: -6px;
}
</style>
