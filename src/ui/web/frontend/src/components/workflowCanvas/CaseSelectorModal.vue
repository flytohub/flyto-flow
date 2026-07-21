<template>
  <div v-if="show" class="case-selector-modal" @click.self="$emit('cancel')">
    <div class="case-selector-panel">
      <div class="case-selector-title">{{ $t('workflow.caseSelector.title') }}</div>
      <button
        v-for="(c, i) in caseOptions"
        :key="`case-select-${c.id || i}`"
        class="case-selector-option"
        @click.stop="$emit('select', c)"
      >
        <span class="case-selector-dot" :style="{ background: c.color }"></span>
        {{ c.label || c.value || $t('workflow.caseSelector.caseLabel', { index: i + 1 }) }}
      </button>
      <button class="case-selector-cancel" @click="$emit('cancel')">
        {{ $t('workflow.caseSelector.cancel') }}
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: { type: Boolean, default: false },
  caseOptions: { type: Array, default: () => [] }
})

defineEmits(['select', 'cancel'])
</script>

<style scoped>
.case-selector-modal {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(4px);
  z-index: 20;
}

.case-selector-panel {
  background: #1e293b;
  border: 1px solid #374151;
  border-radius: 12px;
  padding: 14px;
  min-width: 200px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
  transform: translateY(-6px);
  animation: caseSelectorIn 0.18s ease-out;
}

.case-selector-title {
  font-size: 12px;
  color: #cbd5f5;
  margin-bottom: 8px;
  font-weight: 600;
}

.case-selector-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  color: #e2e8f0;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
}

.case-selector-option:hover {
  background: rgba(236, 72, 153, 0.18);
}

.case-selector-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.case-selector-cancel {
  margin-top: 8px;
  width: 100%;
  background: #0f172a;
  border: 1px solid #334155;
  color: #94a3b8;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
}

.case-selector-cancel:hover {
  color: #e2e8f0;
  border-color: #475569;
}

@keyframes caseSelectorIn {
  from {
    opacity: 0;
    transform: translateY(4px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(-6px) scale(1);
  }
}
</style>
