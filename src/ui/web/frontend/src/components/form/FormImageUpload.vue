<template>
  <div
    class="image-upload"
    :class="{ 'has-image': modelValue, dragging: isDragging }"
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
    <template v-if="modelValue && preview">
      <img :src="preview" class="image-preview" alt="Preview" />
      <div class="image-overlay">
        <span class="file-name">{{ modelValue.name }}</span>
        <button type="button" class="file-remove" @click.stop="removeFile">
          <X :size="16" aria-hidden="true" />
        </button>
      </div>
    </template>
    <template v-else>
      <ImageIcon :size="40" aria-hidden="true" />
      <span class="upload-text">{{ $t('simpleToolView.dropOrClick') }}</span>
      <span class="upload-hint">PNG, JPG, GIF, WebP</span>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { Image as ImageIcon, X } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: [File, Object],
    default: null
  },
  accept: {
    type: String,
    default: 'image/*'
  }
})

const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const isDragging = ref(false)
const preview = ref(null)

watch(() => props.modelValue, (file) => {
  if (preview.value) {
    URL.revokeObjectURL(preview.value)
    preview.value = null
  }
  if (file && file.type?.startsWith('image/')) {
    preview.value = URL.createObjectURL(file)
  }
}, { immediate: true })

onUnmounted(() => {
  if (preview.value) {
    URL.revokeObjectURL(preview.value)
  }
})

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
</script>

<style scoped>
.image-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 160px;
  padding: 20px;
  border: 2px dashed #334155;
  border-radius: 12px;
  background: #0f172a;
  cursor: pointer;
  transition: all 0.2s;
  color: #64748b;
  position: relative;
  overflow: hidden;
}

.image-upload:hover,
.image-upload.dragging {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.image-upload.has-image {
  border-style: solid;
  border-color: #10b981;
}

.file-hidden {
  display: none;
}

.upload-text {
  font-size: 14px;
}

.upload-hint {
  font-size: 12px;
  color: #475569;
}

.image-preview {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
  border-radius: 8px;
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
}

.file-name {
  font-size: 13px;
  color: #f1f5f9;
  word-break: break-all;
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
