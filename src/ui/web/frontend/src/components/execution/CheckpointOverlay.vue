<template>
  <Transition name="slide-in">
    <div v-if="visible" class="checkpoint-overlay">
      <div class="checkpoint-header">
        <div class="checkpoint-icon">
          <CirclePause :size="20" />
        </div>
        <div class="checkpoint-title">{{ $t('debug.checkpoint.humanCheckpoint') }}</div>
      </div>

      <div class="checkpoint-progress">
        <span class="progress-current">{{ currentIndex }}</span>
        <span class="progress-separator">/</span>
        <span class="progress-total">{{ totalItems }}</span>
        <span class="progress-label">{{ $t('debug.checkpoint.items') }}</span>
      </div>

      <div v-if="itemPreview" class="checkpoint-preview">
        <div class="preview-title">{{ $t('debug.checkpoint.currentItemPreview') }}</div>
        <div class="preview-content custom-scrollbar">
          <div
            v-for="(value, key) in itemPreview"
            :key="key"
            class="preview-item"
          >
            <span class="preview-key">{{ key }}:</span>
            <span class="preview-value">{{ formatValue(value) }}</span>
          </div>
        </div>
      </div>

      <div class="checkpoint-actions">
        <button
          class="btn-continue"
          :disabled="loading"
          @click="handleContinue"
          aria-label="Continue"
        >
          <Play :size="16" />
          <span>{{ $t('debug.checkpoint.continue') }}</span>
        </button>

        <div class="bypass-dropdown" ref="dropdownRef">
          <button
            class="btn-bypass"
            :disabled="loading"
            @click="toggleDropdown"
            aria-label="Run all"
          >
            <FastForward :size="16" />
            <span>{{ $t('debug.checkpoint.runAll') }}</span>
            <ChevronDown :size="14" />
          </button>

          <Transition name="dropdown">
            <div v-if="dropdownOpen" class="bypass-menu">
              <button
                class="bypass-option"
                @click="handleBypass('this_run')"
              >
                <div class="option-title">{{ $t('debug.checkpoint.thisRunOnly') }}</div>
                <div class="option-desc">{{ $t('debug.checkpoint.thisRunOnlyDesc', { count: remainingItems }) }}</div>
              </button>
              <button
                class="bypass-option"
                @click="handleBypass('this_version')"
              >
                <div class="option-title">{{ $t('debug.checkpoint.thisVersionOnly') }}</div>
                <div class="option-desc">{{ $t('debug.checkpoint.thisVersionOnlyDesc') }}</div>
              </button>
            </div>
          </Transition>
        </div>
      </div>

      <div v-if="loading" class="checkpoint-loading">
        <Loader2 :size="16" class="animate-spin" />
        <span>{{ $t('debug.checkpoint.processing') }}</span>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { CirclePause, Play, FastForward, ChevronDown, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  currentIndex: {
    type: Number,
    default: 1
  },
  totalItems: {
    type: Number,
    default: 1
  },
  itemPreview: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['continue', 'bypass'])

const dropdownOpen = ref(false)
const dropdownRef = ref(null)

const remainingItems = computed(() => {
  return Math.max(0, props.totalItems - props.currentIndex)
})

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function handleContinue() {
  emit('continue')
}

function handleBypass(scope) {
  dropdownOpen.value = false
  emit('bypass', scope)
}

function formatValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

// Close dropdown when clicking outside
function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    dropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.checkpoint-overlay {
  position: fixed;
  top: 80px;
  right: 24px;
  width: 320px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  overflow: hidden;
}

.checkpoint-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  background: rgba(239, 68, 68, 0.1);
  border-bottom: 1px solid rgba(239, 68, 68, 0.2);
}

.checkpoint-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  color: #ef4444;
}

.checkpoint-title {
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}

.checkpoint-progress {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 16px;
  border-bottom: 1px solid #334155;
}

.progress-current {
  font-size: 28px;
  font-weight: 700;
  color: #8b5cf6;
}

.progress-separator {
  font-size: 20px;
  color: #64748b;
}

.progress-total {
  font-size: 20px;
  font-weight: 500;
  color: #94a3b8;
}

.progress-label {
  font-size: 13px;
  color: #64748b;
  margin-left: 8px;
}

.checkpoint-preview {
  padding: 16px;
  border-bottom: 1px solid #334155;
}

.preview-title {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.preview-content {
  max-height: 120px;
  overflow-y: auto;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 8px;
  padding: 10px;
}

.preview-item {
  display: flex;
  gap: 8px;
  font-size: 12px;
  padding: 4px 0;
}

.preview-item + .preview-item {
  border-top: 1px solid #1e293b;
}

.preview-key {
  color: #94a3b8;
  flex-shrink: 0;
}

.preview-value {
  color: #e2e8f0;
  word-break: break-all;
}

.checkpoint-actions {
  display: flex;
  gap: 10px;
  padding: 16px;
}

.btn-continue {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-continue:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.btn-continue:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bypass-dropdown {
  position: relative;
}

.btn-bypass {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 14px;
  background: rgba(71, 85, 105, 0.5);
  border: 1px solid #475569;
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-bypass:hover:not(:disabled) {
  background: rgba(71, 85, 105, 0.8);
  border-color: #64748b;
}

.btn-bypass:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bypass-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  width: 260px;
  margin-bottom: 8px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.bypass-option {
  width: 100%;
  padding: 12px 14px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s;
}

.bypass-option:hover {
  background: rgba(139, 92, 246, 0.1);
}

.bypass-option + .bypass-option {
  border-top: 1px solid #334155;
}

.option-title {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 2px;
}

.option-desc {
  font-size: 11px;
  color: #64748b;
}

.checkpoint-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: rgba(139, 92, 246, 0.1);
  color: #a78bfa;
  font-size: 12px;
}

/* Animations */
.slide-in-enter-active,
.slide-in-leave-active {
  transition: all 0.3s ease;
}

.slide-in-enter-from,
.slide-in-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
