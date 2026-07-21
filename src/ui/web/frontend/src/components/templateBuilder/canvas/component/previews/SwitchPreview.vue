<template>
  <div class="switch-preview">
    <label class="switch-label">
      <div class="switch-container">
        <input
          ref="inputRef"
          type="checkbox"
          :checked="localValue"
          :disabled="!editable"
          class="switch-input"
          @change="handleChange"
        />
        <span :class="['switch-track', { checked: localValue }]">
          <span class="switch-thumb" />
        </span>
      </div>
      <span v-if="component.label" class="switch-text">
        {{ component.label }}
        <span v-if="component.validation?.required" class="required-mark">*</span>
      </span>
    </label>
    <PreviewHelp :text="component.helpText" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import PreviewHelp from '@/components/common/PreviewHelp.vue'

const props = defineProps({
  component: {
    type: Object,
    required: true
  },
  editable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update', 'focus', 'blur'])

const inputRef = ref(null)
const localValue = ref(props.component.default || false)

watch(() => props.component.default, (newVal) => {
  localValue.value = newVal || false
})

function handleChange(e) {
  localValue.value = e.target.checked
  emit('update', { field: 'default', value: e.target.checked })
}

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.switch-preview {
  width: 100%;
}

.switch-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.switch-container {
  position: relative;
  display: inline-block;
}

.switch-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-track {
  display: block;
  width: 44px;
  height: 24px;
  background: #475569;
  border-radius: 12px;
  transition: background 0.2s;
  position: relative;
}

.switch-track.checked {
  background: #8B5CF6;
}

.switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.switch-track.checked .switch-thumb {
  transform: translateX(20px);
}

.switch-input:disabled + .switch-track {
  opacity: 0.5;
  cursor: not-allowed;
}

.switch-text {
  font-size: 13px;
  color: #f1f5f9;
}

.required-mark {
  color: #ef4444;
  margin-left: 2px;
}
</style>
