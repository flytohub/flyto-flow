<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="show"
        @click="$emit('close')"
        @keydown.esc="$emit('close')"
        class="ratio-dialog-overlay"
      >
        <div @click.stop class="ratio-dialog" role="dialog" aria-modal="true" aria-labelledby="grid-edit-dialog-title">
          <!-- Glow line at top -->
          <div class="ratio-dialog-glow" aria-hidden="true"></div>

          <!-- Header -->
          <div class="ratio-dialog-header">
            <div class="ratio-header-icon" aria-hidden="true">
              <LayoutGrid :size="18" />
            </div>
            <h4 id="grid-edit-dialog-title" class="ratio-header-title">{{ $t('templateBuilder.dialog.editGridRatio') }}</h4>
            <button @click="$emit('close')" class="ratio-close-btn" :aria-label="t('accessibility.closeDialog')">
              <X :size="18" aria-hidden="true" />
            </button>
          </div>

          <!-- Body -->
          <div class="ratio-dialog-body">
            <p class="ratio-description">
              {{ $t('templateBuilder.dialog.editGridRatioMessage') }}
            </p>

            <!-- Column inputs -->
            <div class="ratio-columns">
              <div
                v-for="(value, index) in localGridValues"
                :key="index"
                class="ratio-column-item"
              >
                <label class="ratio-column-label">
                  <span class="ratio-column-num">{{ index + 1 }}</span>
                  {{ $t('templateBuilder.dialog.column') }}
                </label>
                <div class="ratio-input-wrapper">
                  <NumberInput
                    v-model="localGridValues[index]"
                    :min="1"
                    :max="12"
                    inputClass="ratio-input"
                  />
                  <span class="ratio-input-unit">/12</span>
                </div>
              </div>
            </div>

            <!-- Visual preview -->
            <div class="ratio-preview">
              <div class="ratio-preview-label">{{ $t('templateBuilder.dialog.preview') }}</div>
              <div class="ratio-preview-grid">
                <div
                  v-for="(value, index) in localGridValues"
                  :key="index"
                  class="ratio-preview-col"
                  :style="{ flex: value }"
                >
                  <span class="ratio-preview-text">{{ value }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="ratio-dialog-footer">
            <div class="ratio-total" :class="{ 'valid': gridSum === 12, 'invalid': gridSum !== 12 }" role="status" aria-live="polite">
              <span class="ratio-total-label">{{ $t('templateBuilder.dialog.total') }}</span>
              <span class="ratio-total-value">{{ gridSum }}</span>
              <span class="ratio-total-max">/ 12</span>
              <component :is="gridSum === 12 ? CheckCircle : AlertTriangle" :size="16" class="ratio-total-icon" aria-hidden="true" />
            </div>
            <div class="ratio-actions">
              <button @click="$emit('close')" class="ratio-btn cancel">
                {{ $t('common.cancel') }}
              </button>
              <button
                @click="handleSave"
                :disabled="gridSum !== 12"
                class="ratio-btn confirm"
              >
                <CheckCircle :size="16" aria-hidden="true" />
                {{ $t('common.confirm') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { LayoutGrid, X, CheckCircle, AlertTriangle } from 'lucide-vue-next'
import NumberInput from '@/components/common/NumberInput.vue'

const { t } = useI18n()

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  gridValues: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'save'])

const localGridValues = ref([])

// Sync local values with props
watch(() => props.gridValues, (newVal) => {
  localGridValues.value = [...newVal]
}, { immediate: true, deep: true })

// Calculate grid sum
const gridSum = computed(() => {
  return localGridValues.value.reduce((sum, val) => sum + (parseInt(val) || 0), 0)
})

function handleSave() {
  if (gridSum.value === 12) {
    emit('save', localGridValues.value.map(v => parseInt(v)))
  }
}
</script>

<style scoped>
.ratio-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.ratio-dialog {
  position: relative;
  width: 400px;
  max-width: 90vw;
  background: linear-gradient(180deg, #0c1222 0%, #070b14 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 20px;
  overflow: hidden;
  box-shadow:
    0 25px 80px rgba(0, 0, 0, 0.6),
    0 0 60px rgba(139, 92, 246, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.ratio-dialog-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, #8B5CF6 15%, #06B6D4 50%, #8B5CF6 85%, transparent 100%);
}

.ratio-dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.4);
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(6, 182, 212, 0.05) 100%);
}

.ratio-header-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.ratio-header-title {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
}

.ratio-close-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.4);
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.ratio-close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}

.ratio-dialog-body {
  padding: 24px 20px;
}

.ratio-description {
  margin: 0 0 20px;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}

.ratio-columns {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.ratio-column-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ratio-column-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}

.ratio-column-num {
  width: 20px;
  height: 20px;
  border-radius: 6px;
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  color: white;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ratio-input-wrapper {
  position: relative;
}

.ratio-input {
  width: 100%;
  padding: 10px 40px 10px 14px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 10px;
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 600;
  text-align: center;
  transition: all 0.2s;
}

.ratio-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.ratio-input-unit {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  color: #64748b;
}

/* Preview */
.ratio-preview {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 12px;
  padding: 16px;
}

.ratio-preview-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.ratio-preview-grid {
  display: flex;
  gap: 8px;
  height: 48px;
}

.ratio-preview-col {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.1) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.ratio-preview-text {
  font-size: 14px;
  font-weight: 700;
  color: #a78bfa;
}

/* Footer */
.ratio-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-top: 1px solid rgba(71, 85, 105, 0.4);
  background: rgba(15, 23, 42, 0.4);
}

.ratio-total {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  transition: all 0.3s;
}

.ratio-total.valid {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.ratio-total.invalid {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.ratio-total-label {
  font-size: 12px;
  color: #94a3b8;
}

.ratio-total-value {
  font-size: 16px;
  font-weight: 700;
}

.ratio-total.valid .ratio-total-value {
  color: #34d399;
}

.ratio-total.invalid .ratio-total-value {
  color: #f87171;
}

.ratio-total-max {
  font-size: 12px;
  color: #64748b;
}

.ratio-total-icon {
  margin-left: 4px;
}

.ratio-total.valid .ratio-total-icon {
  color: #34d399;
}

.ratio-total.invalid .ratio-total-icon {
  color: #f87171;
}

.ratio-actions {
  display: flex;
  gap: 10px;
}

.ratio-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.ratio-btn.cancel {
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #94a3b8;
}

.ratio-btn.cancel:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.ratio-btn.confirm {
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.ratio-btn.confirm:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
}

.ratio-btn.confirm:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: all 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .ratio-dialog,
.modal-fade-leave-to .ratio-dialog {
  transform: scale(0.95) translateY(-20px);
}
</style>
