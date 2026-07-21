<template>
  <div class="expression-input">
    <div class="expression-prefix" aria-hidden="true">
      <Code :size="12" />
      <span>$</span>
    </div>
    <input
      v-model="model"
      :placeholder="t('valueSource.expressionPlaceholder')"
      class="expression-field"
      :class="{ 'has-expand': !readonly }"
      :readonly="readonly"
      @input="$emit('input')"
    />
    <!-- Expand button to open full expression editor -->
    <button
      v-if="!readonly"
      @click="$emit('open-editor')"
      class="expand-btn"
      :title="t('expression.openEditor')"
      type="button"
    >
      <Maximize2 :size="14" aria-hidden="true" />
    </button>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { Code, Maximize2 } from 'lucide-vue-next'

const { t } = useI18n()

const model = defineModel({ type: [String, Number], default: '' })

defineProps({
  readonly: { type: Boolean, default: false },
})

defineEmits(['input', 'open-editor'])
</script>

<style scoped>
.expression-input {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
}

.expression-prefix {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 12px;
  background: rgba(139, 92, 246, 0.15);
  border-right: 1px solid rgba(71, 85, 105, 0.5);
  color: #a78bfa;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 13px;
  font-weight: 600;
}

.expression-field {
  flex: 1;
  padding: 10px 12px;
  background: transparent;
  border: none;
  outline: none;
  color: #e2e8f0;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 13px;
}

.expression-field::placeholder {
  color: #475569;
}

.expression-field.has-expand {
  padding-right: 36px;
}

.expression-field[readonly] {
  cursor: default;
  opacity: 0.8;
  padding-right: 12px;
}

.expand-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 4px;
  color: #a78bfa;
  cursor: pointer;
  transition: all 0.2s;
}

.expand-btn:hover {
  background: rgba(139, 92, 246, 0.25);
  border-color: rgba(139, 92, 246, 0.5);
  color: #c4b5fd;
}

.expand-btn:focus-visible {
  outline: 2px solid #8B5CF6;
  outline-offset: 2px;
}
</style>
