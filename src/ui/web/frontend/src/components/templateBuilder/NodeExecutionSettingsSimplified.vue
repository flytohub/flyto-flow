<script setup>
/**
 * NodeExecutionSettingsSimplified
 *
 * Simplified execution settings - collapsed by default
 * Only shows when user needs to configure timeout, retry, etc.
 */
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Settings, ChevronRight, Clock, AlertCircle, Zap, RefreshCw, Repeat, Filter } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import NumberInput from '../common/NumberInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'

const { t } = useI18n()

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:node', 'update:settings'])

// Collapsed by default
const isOpen = ref(false)

// Auto-expand if non-default values exist
watch(() => props.node, (node) => {
  if (node?.data) {
    const d = node.data
    const hasCustomSettings =
      (d.timeoutMs && d.timeoutMs !== 30000) ||
      d.onError === 'continue' ||
      d.onError === 'retry' ||
      d.parallel ||
      d.retry?.enabled ||
      d.foreach ||
      d.runIf ||
      d.skipIf

    if (hasCustomSettings) {
      isOpen.value = true
    }
  }
}, { immediate: true })

// Local settings
const settings = computed(() => {
  const d = props.node?.data || {}
  return {
    timeoutMs: d.timeoutMs ?? d.timeout ?? 30000,
    onError: d.onError || 'stop',
    parallel: d.parallel || false,
    retryEnabled: d.retry?.enabled || false,
    retryMax: d.retry?.max_attempts || 3,
    foreach: d.foreach || '',
    foreachAs: d.foreachAs || d.as || 'item',
    runIf: d.runIf || '',
    skipIf: d.skipIf || ''
  }
})

// Badge showing configured items
const badge = computed(() => {
  const s = settings.value
  let count = 0
  if (s.timeoutMs !== 30000) count++
  if (s.onError !== 'stop') count++
  if (s.parallel) count++
  if (s.retryEnabled) count++
  if (s.foreach) count++
  if (s.runIf || s.skipIf) count++
  return count || null
})

function update(field, value) {
  if (props.readOnly) return

  const updatedData = { ...props.node.data }

  if (field === 'retryEnabled') {
    updatedData.retry = value
      ? { enabled: true, maxAttempts: 3, strategy: 'exponential', initialDelayMs: 1000 }
      : { enabled: false }
  } else if (field === 'retryMax') {
    updatedData.retry = { ...updatedData.retry, maxAttempts: value }
  } else {
    updatedData[field] = value
  }

  emit('update:node', { ...props.node, data: updatedData })
  emit('update:settings', updatedData)
}
</script>

<template>
  <div class="exec-settings">
    <!-- Collapsible Header -->
    <button
      type="button"
      class="settings-header"
      :class="{ open: isOpen }"
      @click="isOpen = !isOpen"
    >
      <div class="header-left">
        <Settings :size="14" />
        <span>{{ t('node.settings.execution', 'Execution') }}</span>
        <span v-if="badge" class="badge">{{ badge }}</span>
      </div>
      <ChevronRight
        :size="14"
        class="chevron"
        :class="{ rotated: isOpen }"
      />
    </button>

    <!-- Collapsible Content -->
    <div class="settings-body" :class="{ open: isOpen }">
      <div class="settings-grid">
        <!-- Row 1: Timeout + On Error -->
        <div class="row">
          <div class="field">
            <label><Clock :size="12" /> {{ t('node.settings.timeout', 'Timeout') }}</label>
            <div class="input-row">
              <NumberInput
                :modelValue="settings.timeoutMs"
                @update:modelValue="update('timeoutMs', $event)"
                :min="0"
                :step="1000"
                :disabled="readOnly"
                inputClass="input-sm"
              />
              <span class="suffix">ms</span>
            </div>
          </div>

          <div class="field">
            <label><AlertCircle :size="12" /> {{ t('node.settings.onError', 'On Error') }}</label>
            <AppSelect
              :modelValue="settings.onError"
              @update:modelValue="update('onError', $event)"
              :disabled="readOnly"
              :options="[
                { value: 'stop', label: t('node.settings.stop', 'Stop') },
                { value: 'continue', label: t('node.settings.continue', 'Continue') },
                { value: 'retry', label: t('node.settings.retry', 'Retry') }
              ]"
              size="sm"
            />
          </div>
        </div>

        <!-- Row 2: Parallel + Retry -->
        <div class="row">
          <label class="checkbox-field">
            <input
              type="checkbox"
              :checked="settings.parallel"
              @change="update('parallel', $event.target.checked)"
              :disabled="readOnly"
            />
            <Zap :size="12" />
            {{ t('node.settings.parallel', 'Parallel') }}
          </label>

          <label class="checkbox-field">
            <input
              type="checkbox"
              :checked="settings.retryEnabled"
              @change="update('retryEnabled', $event.target.checked)"
              :disabled="readOnly"
            />
            <RefreshCw :size="12" />
            {{ t('node.settings.retry', 'Retry') }}
            <NumberInput
              v-if="settings.retryEnabled"
              :modelValue="settings.retryMax"
              @update:modelValue="update('retryMax', $event)"
              :min="1"
              :max="10"
              :disabled="readOnly"
              inputClass="input-xs"
            />
          </label>
        </div>

        <!-- Row 3: Foreach (optional) -->
        <div class="field full-width">
          <label><Repeat :size="12" /> {{ t('node.settings.foreach', 'For Each') }}</label>
          <div class="input-row">
            <AppInput
              :modelValue="settings.foreach"
              @update:modelValue="update('foreach', $event)"
              :placeholder="t('node.settings.foreachPlaceholder', '${items}')"
              :readonly="readOnly"
              size="sm"
            />
            <template v-if="settings.foreach">
              <span class="as-label">as</span>
              <AppInput
                :modelValue="settings.foreachAs"
                @update:modelValue="update('foreachAs', $event)"
                placeholder="item"
                :readonly="readOnly"
                size="sm"
              />
            </template>
          </div>
        </div>

        <!-- Row 4: Conditionals (optional) -->
        <div class="field full-width">
          <label><Filter :size="12" /> {{ t('node.settings.conditions', 'Conditions') }}</label>
          <div class="conditions-row">
            <AppInput
              :modelValue="settings.runIf"
              @update:modelValue="update('runIf', $event)"
              :placeholder="t('node.settings.runIf', 'Run if...')"
              :readonly="readOnly"
              size="sm"
            />
            <AppInput
              :modelValue="settings.skipIf"
              @update:modelValue="update('skipIf', $event)"
              :placeholder="t('node.settings.skipIf', 'Skip if...')"
              :readonly="readOnly"
              size="sm"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.exec-settings {
  margin-top: 16px;
  border: 1px solid var(--border-secondary, #334155);
  border-radius: 8px;
  overflow: hidden;
}

/* Header */
.settings-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-secondary, rgba(30, 41, 59, 0.5));
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}

.settings-header:hover {
  background: var(--bg-hover, rgba(139, 92, 246, 0.1));
}

.settings-header.open {
  border-bottom: 1px solid var(--border-secondary, #334155);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #94a3b8);
}

.badge {
  padding: 2px 6px;
  border-radius: 10px;
  background: var(--primary-muted, rgba(139, 92, 246, 0.2));
  color: var(--primary-light, #c4b5fd);
  font-size: 10px;
}

.chevron {
  color: var(--text-muted, #64748b);
  transition: transform 0.2s;
}

.chevron.rotated {
  transform: rotate(90deg);
}

/* Body */
.settings-body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.25s ease;
}

.settings-body.open {
  max-height: 400px;
}

.settings-grid {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Rows */
.row {
  display: flex;
  gap: 12px;
}

.row > * {
  flex: 1;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field.full-width {
  width: 100%;
}

.field label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted, #64748b);
}

/* Inputs */
.input-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.input-sm,
.input-text {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid var(--border-secondary, #334155);
  border-radius: 6px;
  background: var(--bg-tertiary, rgba(15, 23, 42, 0.6));
  color: var(--text-primary, #f1f5f9);
  font-size: 12px;
}

.input-sm:focus,
.input-text:focus {
  outline: none;
  border-color: var(--primary, #8B5CF6);
}

.input-xs {
  width: 50px;
  padding: 4px 8px;
  margin-left: 8px;
  border: 1px solid var(--border-secondary, #334155);
  border-radius: 4px;
  background: var(--bg-tertiary, rgba(15, 23, 42, 0.6));
  color: var(--text-primary, #f1f5f9);
  font-size: 11px;
}

.input-short {
  max-width: 80px;
}

.suffix {
  font-size: 11px;
  color: var(--text-muted, #64748b);
}

.as-label {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  padding: 0 4px;
}

/* Checkbox */
.checkbox-field {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #94a3b8);
  cursor: pointer;
}

.checkbox-field input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--primary, #8B5CF6);
}

/* Conditions */
.conditions-row {
  display: flex;
  gap: 8px;
}

.conditions-row .input-text {
  flex: 1;
}
</style>
