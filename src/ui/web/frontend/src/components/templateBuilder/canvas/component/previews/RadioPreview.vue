<template>
  <div class="radio-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <div :class="['radio-group', `layout-${component.layout || 'vertical'}`]">
      <label
        v-for="option in normalizedOptions"
        :key="option.value"
        class="radio-option"
      >
        <input
          type="radio"
          :name="component.id"
          :value="option.value"
          :checked="localValue === option.value"
          :disabled="!editable"
          class="radio-input"
          @change="handleChange(option.value)"
        />
        <span class="radio-label">{{ option.label }}</span>
      </label>
    </div>
    <PreviewHelp :text="component.helpText" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import PreviewLabel from '@/components/common/PreviewLabel.vue'
import PreviewHelp from '@/components/common/PreviewHelp.vue'

const props = defineProps({
  component: {
    type: Object,
    required: true
  },
  editable: {
    type: Boolean,
    default: true
  },
  hideLabel: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update', 'focus', 'blur'])

const localValue = ref(props.component.default || '')

const normalizedOptions = computed(() => {
  const options = props.component.options || []
  return options.map(opt => {
    if (typeof opt === 'string') {
      return { value: opt, label: opt }
    }
    return opt
  })
})

watch(() => props.component.default, (newVal) => {
  localValue.value = newVal || ''
})

function handleChange(value) {
  localValue.value = value
  emit('update', { field: 'default', value })
}
</script>

<style scoped>
.radio-preview {
  width: 100%;
}

.radio-group {
  display: flex;
  gap: 12px;
}

.radio-group.layout-vertical {
  flex-direction: column;
  gap: 8px;
}

.radio-group.layout-horizontal {
  flex-direction: row;
  flex-wrap: wrap;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio-input {
  width: 16px;
  height: 16px;
  accent-color: #8B5CF6;
  cursor: pointer;
}

.radio-input:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.radio-label {
  font-size: 13px;
  color: #e2e8f0;
}
</style>
