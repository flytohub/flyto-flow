<template>
  <div class="empty-canvas-state">
    <!-- Button wrapper with rings -->
    <div class="btn-wrapper">
      <div class="glow-ring ring-outer" aria-hidden="true"></div>
      <div class="glow-ring ring-inner" aria-hidden="true"></div>
      <button @click="$emit('add-node')" class="add-btn" :aria-label="t('workflow.addFirstStep')">
        <Plus :size="28" aria-hidden="true" />
      </button>
    </div>

    <!-- Hint text -->
    <p class="hint-text">{{ t('workflow.addFirstStep') }}</p>
  </div>
</template>

<script setup>
import { Plus } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineEmits(['add-node'])
</script>

<style scoped>
.empty-canvas-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 5;
}

/* Wrapper to center rings around button */
.btn-wrapper {
  position: relative;
  width: 130px;
  height: 130px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Glow rings */
.glow-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid;
  pointer-events: none;
}

.ring-inner {
  width: 100px;
  height: 100px;
  border-width: 2px;
  border-color: rgba(139, 92, 246, 0.6);
  animation: ring-pulse 2s ease-in-out infinite;
}

.ring-outer {
  width: 140px;
  height: 140px;
  border-width: 2px;
  border-color: rgba(139, 92, 246, 0.4);
  animation: ring-pulse 2s ease-in-out infinite 0.2s;
}

@keyframes ring-pulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(0.95);
    opacity: 0.3;
  }
  10% {
    transform: translate(-50%, -50%) scale(1.15);
    opacity: 1;
  }
  25% {
    transform: translate(-50%, -50%) scale(0.98);
    opacity: 0.5;
  }
  40% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.9;
  }
  60% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.4;
  }
}

/* Add button - circle with dashed border */
.add-btn {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 2px dashed rgba(139, 92, 246, 0.5);
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(8px);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8B5CF6;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
}

.add-btn:hover {
  border-color: #8B5CF6;
  border-style: solid;
  background: rgba(139, 92, 246, 0.15);
  transform: scale(1.08);
  box-shadow:
    0 0 30px rgba(139, 92, 246, 0.4),
    0 0 60px rgba(139, 92, 246, 0.2);
}

.add-btn:focus-visible {
  outline: 2px solid #8B5CF6;
  outline-offset: 4px;
  border-color: #8B5CF6;
  border-style: solid;
}

.add-btn:hover svg {
  transform: rotate(90deg);
}

.add-btn svg {
  transition: transform 0.3s ease;
}

/* Hint text */
.hint-text {
  margin-top: 16px;
  font-size: 13px;
  color: #64748b;
  text-align: center;
}
</style>
