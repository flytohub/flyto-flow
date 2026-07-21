<template>
  <div :class="['option-item', { half: half }]">
    <label v-if="label" class="option-label">{{ label }}</label>
    <input
      v-if="inputType === 'text'"
      :value="modelValue"
      @input="$emit('update:modelValue', processValue($event.target.value))"
      type="text"
      :class="['prop-input-sm', { mono: monospace }]"
      :placeholder="placeholder"
    />
    <NumberInput
      v-else-if="inputType === 'number'"
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      inputClass="prop-input-sm"
      :placeholder="placeholder"
    />
    <AppSelect
      v-else-if="inputType === 'select'"
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :options="options"
      size="sm"
    />
  </div>
</template>

<script setup>
import NumberInput from '@/components/common/NumberInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  inputType: {
    type: String,
    default: 'text' // text, number, select
  },
  placeholder: {
    type: String,
    default: ''
  },
  monospace: {
    type: Boolean,
    default: false
  },
  half: {
    type: Boolean,
    default: false
  },
  options: {
    type: Array,
    default: () => []
  },
  parseNumber: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue'])

function processValue(value) {
  if (props.parseNumber && props.inputType === 'number') {
    return value ? Number(value) : null
  }
  return value
}
</script>

<style scoped>
.option-item {
  margin-bottom: 12px;
}

.option-item:last-child {
  margin-bottom: 0;
}

.option-item.half {
  flex: 1;
}

.option-label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  margin-bottom: 6px;
}

.prop-input-sm {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  color: #f1f5f9;
  font-size: 12px;
  transition: all 0.2s;
}

.prop-input-sm:focus {
  outline: none;
  border-color: #8B5CF6;
}

.prop-input-sm.mono {
  font-family: 'SF Mono', Monaco, monospace;
}
</style>
