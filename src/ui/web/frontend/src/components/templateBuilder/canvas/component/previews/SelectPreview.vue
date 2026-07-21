<template>
  <div class="select-preview">
    <PreviewLabel
      :label="component.label"
      :required="component.validation?.required"
    />
    <AppSelect
      :modelValue="localValue"
      :options="normalizedOptions"
      :placeholder="component.placeholder || 'Select an option'"
      :multiple="component.multiple"
      :disabled="!editable"
      size="sm"
      @update:modelValue="handleSelectChange"
    />
    <PreviewHelp :text="component.helpText" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import PreviewLabel from '@/components/common/PreviewLabel.vue'
import PreviewHelp from '@/components/common/PreviewHelp.vue'
import AppSelect from '@/components/common/AppSelect.vue'

const props = defineProps({
  component: { type: Object, required: true },
  editable: { type: Boolean, default: true }
})

const emit = defineEmits(['update', 'focus', 'blur'])
const localValue = ref(props.component.default || '')

const normalizedOptions = computed(() => {
  const options = props.component.options || []
  return options.map(opt => typeof opt === 'string' ? { value: opt, label: opt } : opt)
})

watch(() => props.component.default, (v) => { localValue.value = v || '' })

function handleSelectChange(value) {
  localValue.value = value
  emit('update', { field: 'default', value })
}
</script>

<style scoped>
.select-preview {
  width: 100%;
  /* Allow AppSelect dropdown to overflow canvas container */
  position: relative;
  z-index: 10;
}
</style>
