<template>
  <div class="file-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <div
      :class="['file-dropzone', { dragover: isDragOver, disabled: !editable }]"
      @dragover.prevent="handleDragOver"
      @dragleave="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        :accept="component.accept"
        :multiple="component.multiple"
        :disabled="!editable"
        class="file-input-hidden"
        @change="handleFileChange"
      />
      <div class="dropzone-content">
        <svg class="upload-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p class="dropzone-text">{{ dropzoneText }}</p>
        <p v-if="component.accept" class="dropzone-accept">{{ acceptText }}</p>
      </div>
    </div>
    <div v-if="selectedFiles.length > 0" class="file-list">
      <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
        <span class="file-name">{{ file.name }}</span>
        <span class="file-size">{{ formatBytes(file.size) }}</span>
        <button
          v-if="editable"
          type="button"
          class="file-remove"
          @click="removeFile(index)"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
    <PreviewHelp :text="component.helpText" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import PreviewLabel from '@/components/common/PreviewLabel.vue'
import PreviewHelp from '@/components/common/PreviewHelp.vue'
import { formatBytes } from '@/utils/format'

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

const fileInputRef = ref(null)
const isDragOver = ref(false)
const selectedFiles = ref([])

const dropzoneText = computed(() => {
  return props.component.multiple
    ? 'Drag files here or click to browse'
    : 'Drag a file here or click to browse'
})

const acceptText = computed(() => {
  const accept = props.component.accept
  if (!accept) return ''
  return `Accepted: ${accept}`
})

function triggerFileInput() {
  if (props.editable) {
    fileInputRef.value?.click()
  }
}

function handleDragOver() {
  if (props.editable) {
    isDragOver.value = true
  }
}

function handleDragLeave() {
  isDragOver.value = false
}

function handleDrop(e) {
  if (!props.editable) return
  isDragOver.value = false
  const files = Array.from(e.dataTransfer.files)
  addFiles(files)
}

function handleFileChange(e) {
  const files = Array.from(e.target.files)
  addFiles(files)
  e.target.value = ''
}

function addFiles(files) {
  if (props.component.multiple) {
    selectedFiles.value = [...selectedFiles.value, ...files]
  } else {
    selectedFiles.value = files.slice(0, 1)
  }
  emit('update', { field: 'files', value: selectedFiles.value })
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1)
  emit('update', { field: 'files', value: selectedFiles.value })
}

</script>

<style scoped>
.file-preview {
  width: 100%;
}

.file-input-hidden {
  display: none;
}

.file-dropzone {
  padding: 24px;
  border: 2px dashed #475569;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.5);
  cursor: pointer;
  transition: all 0.2s;
}

.file-dropzone:hover:not(.disabled) {
  border-color: #8B5CF6;
  background: rgba(139, 92, 246, 0.05);
}

.file-dropzone.dragover {
  border-color: #8B5CF6;
  background: rgba(139, 92, 246, 0.1);
}

.file-dropzone.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  color: #64748b;
}

.dropzone-text {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

.dropzone-accept {
  font-size: 11px;
  color: #64748b;
  margin: 0;
}

.file-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 6px;
}

.file-name {
  flex: 1;
  font-size: 12px;
  color: #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: #64748b;
}

.file-remove {
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #64748b;
  transition: color 0.2s;
}

.file-remove:hover {
  color: #ef4444;
}
</style>
