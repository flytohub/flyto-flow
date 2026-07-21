<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-template-modal-title"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @keydown.esc="close"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="close"
      ></div>

      <!-- Modal -->
      <div class="relative w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 id="edit-template-modal-title" class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('templateForm.editTemplate') }}</h2>
          <button
            @click="close"
            :aria-label="t('accessibility.closeDialog')"
            class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          >
            <X :size="20" aria-hidden="true" />
          </button>
        </div>

        <!-- Body -->
        <form @submit.prevent="submit" class="p-6">
          <div class="flex flex-col sm:flex-row gap-6">
            <!-- Left Column: Icon & Color -->
            <div class="w-full sm:w-44 shrink-0 space-y-4">
              <!-- Icon Upload -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {{ $t('templateForm.templateIcon') }}
                </label>
                <!-- Icon Preview -->
                <div class="relative group inline-block">
                  <!-- Uploading state -->
                  <div
                    v-if="isUploadingIcon"
                    class="w-20 h-20 rounded-xl flex items-center justify-center bg-gradient-to-br from-purple-600 to-indigo-600 shadow-lg"
                  >
                    <Loader2 :size="24" class="animate-spin text-white" />
                  </div>
                  <!-- Has icon -->
                  <TemplateIcon
                    v-else-if="form.iconUrl"
                    :icon-url="form.iconUrl"
                    :color="form.color"
                    size="xl"
                  />
                  <!-- Empty state with color preview -->
                  <div
                    v-else
                    class="w-20 h-20 rounded-xl flex items-center justify-center shadow-lg"
                    :style="{ background: `linear-gradient(135deg, ${form.color}, ${adjustColor(form.color, 30)})` }"
                  >
                    <ImageIcon :size="28" class="text-white/80" />
                  </div>
                  <!-- Remove button -->
                  <button
                    v-if="form.iconUrl && !isUploadingIcon"
                    type="button"
                    @click="removeIcon"
                    :aria-label="t('accessibility.removeIcon')"
                    class="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all shadow-md"
                  >
                    <X :size="12" aria-hidden="true" />
                  </button>
                </div>
                <!-- Upload Button -->
                <label
                  class="mt-2 flex items-center justify-center gap-2 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <Upload :size="14" class="text-gray-500" aria-hidden="true" />
                  <span class="text-gray-600 dark:text-gray-300">
                    {{ form.iconUrl ? $t('templateForm.changeIcon') : $t('templateForm.uploadIcon') }}
                  </span>
                  <input
                    ref="fileInputRef"
                    type="file"
                    accept="image/*"
                    class="hidden"
                    @change="handleFileSelect"
                  />
                </label>
                <p class="text-xs text-gray-400 mt-1 text-center">PNG, JPG, GIF up to 2MB</p>
              </div>

              <!-- Color Picker -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {{ $t('templateForm.templateColor') }}
                </label>
                <ColorPicker v-model="form.color" default-color="#8B5CF6" />
              </div>
            </div>

            <!-- Right Column: Name, Category, Description -->
            <div class="flex-1 space-y-4">
              <!-- Name (Required) -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {{ $t('templateForm.templateName') }} <span class="text-red-500">*</span>
                </label>
                <AppInput
                  v-model="form.name"
                  :placeholder="$t('templateForm.namePlaceholder')"
                  required
                />
              </div>

              <!-- Category (Optional) -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {{ $t('templateForm.category') }}
                </label>
                <AppSelect
                  v-model="form.categoryId"
                  :options="[{ value: '', label: $t('templateForm.selectCategory') }, ...categories.map(cat => ({ value: cat.id, label: cat.name }))]"
                />
              </div>

              <!-- Description (Optional) -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {{ $t('templateForm.description') }}
                </label>
                <AppTextarea
                  v-model="form.description"
                  :rows="4"
                  :placeholder="$t('templateForm.descriptionPlaceholder')"
                />
              </div>
            </div>
          </div>

          <!-- Error Message -->
          <div
            v-if="errorMessage"
            class="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400"
          >
            {{ errorMessage }}
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end gap-3 pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              @click="close"
              class="px-5 py-2.5 min-h-[44px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              type="submit"
              :disabled="!form.name.trim() || isSubmitting || isUploadingIcon"
              class="px-5 py-2.5 min-h-[44px] bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-400"
            >
              <Loader2 v-if="isSubmitting" :size="18" class="animate-spin" aria-hidden="true" />
              <span>{{ isSubmitting ? $t('common.saving') : $t('common.saveChanges') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>

  <!-- Image Cropper Modal -->
  <ImageCropperModal
    v-model="showCropper"
    :image-src="cropperImageSrc"
    :aspect-ratio="1"
    :output-size="256"
    @cropped="handleCropped"
  />
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { X, Loader2, Upload, Image as ImageIcon } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const { t } = useI18n()
import { templatesAPI } from '@/api/templates'
import { storageAPI } from '@/api/storage'
import { DEFAULTS } from '@/config/defaults'
import ImageCropperModal from '@/components/common/ImageCropperModal.vue'
import TemplateIcon from '@/components/common/TemplateIcon.vue'
import ColorPicker from '@/components/common/ColorPicker.vue'

// Adjust color brightness
function adjustColor(hex, amount) {
  if (!hex) return '#8B5CF6'
  let color = hex.replace('#', '')
  if (color.length === 3) {
    color = color.split('').map(c => c + c).join('')
  }
  const num = parseInt(color, 16)
  const r = Math.min(255, Math.max(0, (num >> 16) + amount))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00ff) + amount))
  const b = Math.min(255, Math.max(0, (num & 0x0000ff) + amount))
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
}

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  template: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'updated'])

// Form state
const form = reactive({
  name: '',
  categoryId: '',
  description: '',
  iconUrl: '',
  color: '#8B5CF6'
})

const isSubmitting = ref(false)
const categories = ref([])
const errorMessage = ref('')
const fileInputRef = ref(null)

// Cropper state
const showCropper = ref(false)
const cropperImageSrc = ref('')

// Load categories on mount
onMounted(async () => {
  try {
    const res = await templatesAPI.getCategories()
    categories.value = res.categories || []
  } catch (err) {
    // Error handled silently
  }
})

// Watch for template changes to populate form
watch(() => props.template, (newTemplate) => {
  if (newTemplate) {
    form.name = newTemplate.templateName || newTemplate.name || ''
    form.categoryId = newTemplate.categoryId || ''
    form.description = newTemplate.templateDescription || newTemplate.description || ''
    form.iconUrl = newTemplate.iconUrl || newTemplate.templateIcon || ''
    form.color = newTemplate.color || newTemplate.templateColor || '#8B5CF6'
  }
}, { immediate: true })

// Reset form when modal opens
watch(() => props.modelValue, (isOpen) => {
  if (isOpen && props.template) {
    form.name = props.template.templateName || props.template.name || ''
    form.categoryId = props.template.categoryId || ''
    form.description = props.template.templateDescription || props.template.description || ''
    form.iconUrl = props.template.iconUrl || props.template.templateIcon || ''
    form.color = props.template.color || props.template.templateColor || '#8B5CF6'
    errorMessage.value = ''
  }
})

function close() {
  emit('update:modelValue', false)
}

function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return

  // Validate file type
  if (!file.type.startsWith('image/')) {
    errorMessage.value = 'Please select an image file'
    return
  }

  // Validate file size
  if (file.size > DEFAULTS.LIMITS.MAX_IMAGE_SIZE) {
    errorMessage.value = t('error.imageTooLarge', 'Image must be smaller than 2MB')
    return
  }

  errorMessage.value = ''

  // Read file and open cropper
  const reader = new FileReader()
  reader.onload = (e) => {
    cropperImageSrc.value = e.target.result
    showCropper.value = true
  }
  reader.readAsDataURL(file)

  // Reset file input
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const isUploadingIcon = ref(false)

async function handleCropped(dataUrl) {
  // Upload image to Firebase Storage and get URL
  isUploadingIcon.value = true
  errorMessage.value = ''

  try {
    const result = await storageAPI.uploadImageFromDataUrl(dataUrl, 'template-icon.png', 'template_icon')
    form.iconUrl = result.url
  } catch (err) {
    // Show actual error message for debugging
    const detail = err.response?.data?.detail || err.response?.data?.error || err.userMessage || err.message
    errorMessage.value = detail || t('templateForm.iconUploadError', 'Failed to upload icon. Please try again.')
  } finally {
    isUploadingIcon.value = false
  }
}

function removeIcon() {
  form.iconUrl = ''
}

async function submit() {
  if (!form.name.trim() || isSubmitting.value || !props.template) return

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const templateId = props.template.templateId || props.template.id
    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      categoryId: form.categoryId || null,
      iconUrl: form.iconUrl || null,
      color: form.color || '#8B5CF6'
    }

    const result = await templatesAPI.updateTemplate(templateId, payload)

    if (!result.ok) {
      throw new Error(result.error || 'Failed to update template')
    }

    close()
    emit('updated', templateId)
  } catch (err) {
    errorMessage.value = err.message || 'Failed to update template'
  } finally {
    isSubmitting.value = false
  }
}
</script>
