<template>
  <div class="checkbox-preview">
    <label class="checkbox-label">
      <input
        ref="inputRef"
        type="checkbox"
        :checked="localValue"
        :disabled="!editable"
        class="checkbox-input"
        @change="handleChange"
      />
      <span class="checkbox-text">
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
.checkbox-preview {
  width: 100%;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  accent-color: #8B5CF6;
  cursor: pointer;
}

.checkbox-input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.checkbox-text {
  font-size: 13px;
  color: #f1f5f9;
}

.required-mark {
  color: #ef4444;
  margin-left: 2px;
}
</style>
