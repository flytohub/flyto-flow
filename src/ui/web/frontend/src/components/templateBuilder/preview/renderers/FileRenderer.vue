<template>
  <div class="file-upload">
    <input
      type="file"
      :accept="acceptTypes"
      :multiple="isMultiple"
      :disabled="disabled"
      class="file-upload-input"
      @change="handleFileChange"
    />
    <div class="file-upload-display">
      <Upload :size="18" />
      <span>{{ displayText }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Upload } from 'lucide-vue-next'

const props = defineProps({
  component: { type: Object, required: true },
  modelValue: { type: [File, FileList, Array], default: null },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const fileName = ref('')

const acceptTypes = computed(() => {
  if (props.component.props?.accept) {
    return props.component.props.accept
  }
  if (props.component.type === 'image') {
    return 'image/*'
  }
  return ''
})

const isMultiple = computed(() => props.component.props?.multiple ?? false)

const displayText = computed(() => {
  if (fileName.value) {
    return fileName.value
  }
  return props.component.props?.placeholder || 'Choose file...'
})

function handleFileChange(event) {
  const files = event.target.files
  if (files && files.length > 0) {
    fileName.value = files.length === 1
      ? files[0].name
      : `${files.length} files`
    emit('update:modelValue', files)
  }
}
</script>

<style scoped>
@import './fieldStyles.css';
</style>
