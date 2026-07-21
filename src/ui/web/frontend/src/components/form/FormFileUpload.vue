<template>
  <div
    class="file-upload"
    :class="{ 'has-file': modelValue, dragging: isDragging }"
    @click="triggerFileInput"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="handleFileDrop"
  >
    <input
      ref="fileInput"
      type="file"
      class="file-hidden"
      :accept="accept"
      @change="handleFileSelect"
    />
    <template v-if="modelValue">
      <File :size="24" aria-hidden="true" />
      <span class="file-name">{{ modelValue.name }}</span>
      <span class="file-size">{{ formatFileSize(modelValue.size) }}</span>
      <button type="button" class="file-remove" @click.stop="removeFile">
        <X :size="14" aria-hidden="true" />
      </button>
    </template>
    <template v-else>
      <Upload :size="32" aria-hidden="true" />
      <span class="upload-text">{{ $t('simpleToolView.dropOrClick') }}</span>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, File, X } from 'lucide-vue-next'
import { formatFileSize } from '@/utils/format'

defineProps({
  modelValue: {
    type: [File, Object],
    default: null
  },
  accept: {
    type: String,
    default: '*/*'
  }
})

const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const isDragging = ref(false)

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (file) {
    emit('update:modelValue', file)
  }
}

function handleFileDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer.files?.[0]
  if (file) {
    emit('update:modelValue', file)
  }
}

function removeFile() {
  emit('update:modelValue', null)
}

// formatFileSize imported from @/utils/format
</script>

<style scoped>
.file-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 120px;
  padding: 20px;
  border: 2px dashed #334155;
  border-radius: 12px;
  background: #0f172a;
  cursor: pointer;
  transition: all 0.2s;
  color: #64748b;
}

.file-upload:hover,
.file-upload.dragging {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.file-upload.has-file {
  border-style: solid;
  border-color: #10b981;
}

.file-hidden {
  display: none;
}

.upload-text {
  font-size: 14px;
}

.file-name {
  font-size: 13px;
  color: #f1f5f9;
  word-break: break-all;
}

.file-size {
  font-size: 11px;
  color: #64748b;
}

.file-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
  border: none;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  cursor: pointer;
}

.file-remove:hover {
  background: rgba(239, 68, 68, 0.3);
}
</style>
