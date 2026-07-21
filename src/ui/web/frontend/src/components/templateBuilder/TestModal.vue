<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="show"
        class="test-modal-overlay"
        @click="$emit('close')"
        @keydown.esc="$emit('close')"
      >
        <div class="test-modal" role="dialog" aria-modal="true" aria-labelledby="test-modal-title" @click.stop>
          <div class="modal-header">
            <h2 id="test-modal-title" class="modal-title">
              <FlaskConical :size="20" aria-hidden="true" />
              {{ $t('templateBuilder.test.title') }}
            </h2>
            <button @click="$emit('close')" class="close-btn" :aria-label="t('accessibility.closeModal')">
              <X :size="20" aria-hidden="true" />
            </button>
          </div>
          <div class="modal-body">
            <p class="info-text">{{ $t('templateBuilder.test.developingMessage') }}</p>
            <div v-if="result" class="result-container">
              <h3 class="result-title">{{ $t('templateBuilder.test.submitResult') }}</h3>
              <pre class="result-content">{{ JSON.stringify(result, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { FlaskConical, X } from 'lucide-vue-next'

const { t } = useI18n()

defineProps({
  show: {
    type: Boolean,
    default: false
  },
  result: {
    type: Object,
    default: null
  }
})

defineEmits(['close'])
</script>

<style scoped>
.test-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.test-modal {
  background: #1e293b;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.5);
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #f1f5f9;
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-btn {
  padding: 8px;
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #f1f5f9;
}

.modal-body {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.info-text {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 16px;
}

.result-container {
  margin-top: 24px;
  padding: 16px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.result-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #34d399;
}

.result-content {
  margin: 0;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  color: #a7f3d0;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Transition */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .test-modal,
.modal-fade-leave-active .test-modal {
  transition: transform 0.2s ease;
}

.modal-fade-enter-from .test-modal,
.modal-fade-leave-to .test-modal {
  transform: scale(0.95);
}
</style>
