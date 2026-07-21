<template>
  <div class="number-input-wrapper">
    <input
      ref="inputRef"
      :value="modelValue"
      :placeholder="placeholder"
      :readonly="readonly"
      :disabled="disabled"
      :min="min"
      :max="max"
      :step="step"
      type="number"
      :class="['number-input', inputClass]"
      @input="handleInput"
      @keydown="handleKeydown"
    />
    <div class="spin-buttons" v-if="!readonly && !disabled && showButtons">
      <button type="button" class="spin-btn" @click="increment" tabindex="-1" aria-label="Increase value">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
          <path d="M5 2L9 7H1L5 2Z"/>
        </svg>
      </button>
      <button type="button" class="spin-btn" @click="decrement" tabindex="-1" aria-label="Decrease value">
        <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
          <path d="M5 8L1 3H9L5 8Z"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: 0 },
  placeholder: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  min: { type: Number, default: undefined },
  max: { type: Number, default: undefined },
  step: { type: Number, default: 1 },
  inputClass: { type: String, default: '' },
  showButtons: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])
const inputRef = ref(null)

function clampValue(value) {
  let v = Number(value)
  if (isNaN(v)) return props.min ?? 0
  if (props.min !== undefined && v < props.min) v = props.min
  if (props.max !== undefined && v > props.max) v = props.max
  return v
}

function handleInput(e) {
  const raw = e.target.value
  if (raw === '' || raw === '-') {
    emit('update:modelValue', raw)
    return
  }
  const value = Number(raw)
  if (!isNaN(value)) {
    emit('update:modelValue', value)
  }
}

function handleKeydown(e) {
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    increment()
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    decrement()
  }
}

function increment() {
  const current = Number(props.modelValue) || 0
  emit('update:modelValue', clampValue(current + props.step))
}

function decrement() {
  const current = Number(props.modelValue) || 0
  emit('update:modelValue', clampValue(current - props.step))
}

defineExpose({ focus: () => inputRef.value?.focus() })
</script>

<style scoped>
.number-input-wrapper {
  position: relative;
  display: flex;
  align-items: stretch;
}

.number-input {
  width: 100%;
  padding: 8px 32px 8px 10px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 13px;
  transition: border-color 0.15s ease;
}

.number-input:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
}

.number-input:read-only,
.number-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spin-buttons {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.spin-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 14px;
  padding: 0;
  background: rgba(71, 85, 105, 0.4);
  border: none;
  border-radius: 3px;
  color: rgba(148, 163, 184, 0.8);
  cursor: pointer;
  transition: all 0.15s ease;
}

.spin-btn:hover {
  background: rgba(139, 92, 246, 0.5);
  color: #f1f5f9;
}

.spin-btn:active {
  background: rgba(139, 92, 246, 0.7);
}
</style>
