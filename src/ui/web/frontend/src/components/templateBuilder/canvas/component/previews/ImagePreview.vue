<template>
  <div class="image-preview">
    <div v-if="displaySrc" class="image-container" :style="containerStyle">
      <img
        :src="displaySrc"
        :alt="component.alt || ''"
        :style="imageStyle"
        class="preview-image"
        @error="handleImageError"
      />
      <div
        v-if="editable"
        class="image-overlay"
        role="button"
        tabindex="0"
        :aria-label="$t('templateBuilder.imagePreview.changeImageLabel')"
        @click="openFilePicker"
        @keydown.enter="openFilePicker"
        @keydown.space.prevent="openFilePicker"
      >
        <Upload :size="20" aria-hidden="true" />
        <span>{{ $t('templateBuilder.imagePreview.changeImage') }}</span>
      </div>
    </div>
    <div
      v-else
      class="image-placeholder"
      :style="placeholderStyle"
      :class="{ clickable: editable }"
      :role="editable ? 'button' : undefined"
      :tabindex="editable ? 0 : undefined"
      :aria-label="editable ? $t('templateBuilder.imagePreview.selectImageLabel') : undefined"
      @click="editable && openFilePicker()"
      @keydown.enter="editable && openFilePicker()"
      @keydown.space.prevent="editable && openFilePicker()"
    >
      <svg class="placeholder-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
      <p class="placeholder-text">{{ editable ? $t('templateBuilder.imagePreview.clickToSelect') : $t('templateBuilder.imagePreview.noImageSelected') }}</p>
      <button v-if="editable" class="select-btn">
        <Upload :size="16" aria-hidden="true" />
        {{ $t('templateBuilder.imagePreview.selectImage') }}
      </button>
    </div>

    <!-- URL input for direct URL entry -->
    <div v-if="editable && showUrlInput" class="url-input-container">
      <input
        ref="urlInputRef"
        v-model="urlInput"
        type="text"
        :placeholder="$t('templateBuilder.imagePreview.enterUrl')"
        class="url-input"
        @keyup.enter="applyUrl"
        @blur="handleUrlBlur"
      />
      <button class="url-apply-btn" @click="applyUrl">{{ $t('templateBuilder.imagePreview.apply') }}</button>
    </div>

    <!-- Action buttons -->
    <div v-if="editable && displaySrc" class="image-actions">
      <button class="action-btn" @click="showUrlInput = !showUrlInput" :aria-label="$t('templateBuilder.imagePreview.enterUrlLabel')">
        <Link :size="14" aria-hidden="true" />
      </button>
      <button class="action-btn" @click="openFilePicker" :aria-label="$t('templateBuilder.imagePreview.uploadFile')">
        <Upload :size="14" aria-hidden="true" />
      </button>
      <button class="action-btn danger" @click="clearImage" :aria-label="$t('templateBuilder.imagePreview.removeImage')">
        <Trash2 :size="14" aria-hidden="true" />
      </button>
    </div>

    <p v-if="component.caption" class="image-caption">{{ component.caption }}</p>

    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      class="hidden-input"
      @change="handleFileSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Upload, Link, Trash2 } from 'lucide-vue-next'

const { t } = useI18n()

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

const emit = defineEmits(['update'])

const fileInputRef = ref(null)
const urlInputRef = ref(null)
const hasError = ref(false)
const showUrlInput = ref(false)
const urlInput = ref('')
const localPreview = ref(null)

const displaySrc = computed(() => {
  return localPreview.value || props.component.src
})

const containerStyle = computed(() => {
  const styles = {}
  if (props.component.maxWidth) {
    styles.maxWidth = props.component.maxWidth
  }
  if (props.component.align) {
    if (props.component.align === 'center') {
      styles.marginLeft = 'auto'
      styles.marginRight = 'auto'
    } else if (props.component.align === 'right') {
      styles.marginLeft = 'auto'
    }
  }
  return styles
})

const imageStyle = computed(() => {
  const styles = {
    width: '100%',
    height: 'auto'
  }
  if (props.component.objectFit) {
    styles.objectFit = props.component.objectFit
  }
  if (props.component.borderRadius) {
    styles.borderRadius = props.component.borderRadius
  }
  return styles
})

const placeholderStyle = computed(() => {
  const styles = {}
  if (props.component.height) {
    styles.height = props.component.height
  }
  return styles
})

function handleImageError() {
  hasError.value = true
}

function openFilePicker() {
  fileInputRef.value?.click()
}

function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return

  // Validate file type
  if (!file.type.startsWith('image/')) {
    return
  }

  // Create preview URL
  const reader = new FileReader()
  reader.onload = (e) => {
    localPreview.value = e.target.result
    emit('update', {
      field: 'src',
      value: e.target.result
    })
  }
  reader.readAsDataURL(file)

  // Reset input
  event.target.value = ''
}

function applyUrl() {
  if (urlInput.value.trim()) {
    localPreview.value = urlInput.value.trim()
    emit('update', {
      field: 'src',
      value: urlInput.value.trim()
    })
    showUrlInput.value = false
    urlInput.value = ''
  }
}

function handleUrlBlur() {
  // Small delay to allow click on apply button
  setTimeout(() => {
    if (!urlInput.value.trim()) {
      showUrlInput.value = false
    }
  }, 200)
}

function clearImage() {
  localPreview.value = null
  emit('update', {
    field: 'src',
    value: ''
  })
}
</script>

<style scoped>
.image-preview {
  width: 100%;
}

.image-container {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 8px;
}

.preview-image {
  display: block;
  max-width: 100%;
  height: auto;
}

.image-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}

.image-container:hover .image-overlay {
  opacity: 1;
}

.image-overlay span {
  font-size: 13px;
  font-weight: 500;
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 120px;
  background: rgba(30, 41, 59, 0.5);
  border: 2px dashed #475569;
  border-radius: 8px;
  padding: 24px;
  transition: all 0.2s;
}

.image-placeholder.clickable {
  cursor: pointer;
}

.image-placeholder.clickable:hover {
  border-color: #8B5CF6;
  background: rgba(139, 92, 246, 0.1);
}

.placeholder-icon {
  color: #64748b;
}

.placeholder-text {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.select-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.select-btn:hover {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
  transform: translateY(-1px);
}

.url-input-container {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.url-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  color: #f1f5f9;
  font-size: 13px;
}

.url-input:focus {
  outline: none;
  border-color: #8B5CF6;
}

.url-input::placeholder {
  color: #64748b;
}

.url-apply-btn {
  padding: 8px 14px;
  border-radius: 6px;
  border: none;
  background: #8B5CF6;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.url-apply-btn:hover {
  background: #7c3aed;
}

.image-actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  justify-content: flex-end;
}

.action-btn {
  min-width: 44px;
  min-height: 44px;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: none;
  background: rgba(71, 85, 105, 0.3);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:focus-visible {
  outline: 2px solid #8B5CF6;
  outline-offset: 2px;
}

.action-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.image-caption {
  margin: 8px 0 0;
  font-size: 12px;
  color: #94a3b8;
  text-align: center;
}

.hidden-input {
  display: none;
}
</style>
