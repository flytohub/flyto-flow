<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :aria-label="label"
    :disabled="disabled"
    :class="[
      'toggle-switch',
      modelValue ? 'toggle-on' : 'toggle-off',
      { 'toggle-disabled': disabled }
    ]"
    @click="toggle"
  >
    <span class="toggle-thumb" :class="modelValue ? 'thumb-on' : 'thumb-off'" aria-hidden="true" />
  </button>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  label: {
    type: String,
    default: 'Toggle'
  }
})

const emit = defineEmits(['update:modelValue'])

function toggle() {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}
</script>

<style scoped>
.toggle-switch {
  position: relative;
  width: 48px;
  height: 24px;
  border-radius: 9999px;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s ease;
  flex-shrink: 0;
}

.toggle-on {
  background-color: var(--color-primary-600, #7c3aed);
}

.toggle-off {
  background-color: #d1d5db;
}

:global(.dark .toggle-off) {
  background-color: #4b5563;
}

.toggle-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-switch:focus-visible {
  outline: 2px solid var(--color-primary-500, #8b5cf6);
  outline-offset: 2px;
}

.toggle-thumb {
  position: absolute;
  top: 4px;
  width: 16px;
  height: 16px;
  background-color: white;
  border-radius: 9999px;
  transition: all 0.2s ease;
}

.thumb-on {
  right: 4px;
}

.thumb-off {
  left: 4px;
}
</style>
