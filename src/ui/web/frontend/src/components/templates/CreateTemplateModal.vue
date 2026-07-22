<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-template-title"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @keydown.esc="close"
      >
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="close" />
        <div ref="modalRef" tabindex="-1" class="create-modal animate-scale-in">
          <div class="create-modal-header">
            <div>
              <h2 id="create-template-title" class="text-lg font-bold text-white">{{ $t('createModal.title') }}</h2>
              <p class="text-xs text-gray-400 mt-0.5">{{ $t('myTemplates.subtitle') }}</p>
            </div>
            <button class="create-modal-close" :aria-label="$t('createModal.closeDialog')" @click="close">
              <X :size="18" aria-hidden="true" />
            </button>
          </div>

          <form class="create-modal-body" @submit.prevent="submit">
            <div class="create-icon-section">
              <div class="relative group">
                <TemplateIcon
                  v-if="form.iconUrl"
                  :icon-url="form.iconUrl"
                  size="lg"
                  class="create-icon-preview"
                />
                <div v-else class="create-icon-empty">
                  <Image :size="22" class="text-gray-500" aria-hidden="true" />
                </div>
                <button
                  v-if="form.iconUrl"
                  type="button"
                  class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 hover:bg-red-400 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all shadow-md"
                  :aria-label="$t('createModal.icon.remove')"
                  @click="form.iconUrl = ''"
                >
                  <X :size="10" aria-hidden="true" />
                </button>
              </div>
              <div class="flex-1 min-w-0">
                <label class="create-upload-btn">
                  <Upload :size="15" class="text-purple-400" />
                  <span class="text-[13px] text-gray-300">
                    {{ form.iconUrl ? $t('createModal.icon.change') : $t('createModal.icon.upload') }}
                  </span>
                  <input ref="fileInputRef" type="file" accept="image/*" class="hidden" @change="handleFileSelect" />
                </label>
                <p class="text-[11px] text-gray-500 mt-1.5">{{ $t('createModal.icon.hint') }}</p>
              </div>
            </div>

            <div class="create-field">
              <label for="template-name" class="create-label">
                {{ $t('createModal.name.label') }} <span class="text-red-400">*</span>
              </label>
              <input
                id="template-name"
                v-model="form.name"
                type="text"
                :placeholder="$t('createModal.name.placeholder')"
                required
                autofocus
                class="create-input"
              />
            </div>

            <div class="create-field">
              <label class="create-label">{{ $t('createModal.category.label') }}</label>
              <AppSelect v-model="form.category" :options="categoryOptions" />
            </div>

            <div class="create-field">
              <label for="template-description" class="create-label">{{ $t('createModal.description.label') }}</label>
              <textarea
                id="template-description"
                v-model="form.description"
                rows="3"
                :placeholder="$t('createModal.description.placeholder')"
                class="create-input create-textarea"
              />
            </div>

            <div v-if="errorMessage" role="alert" class="create-error">{{ errorMessage }}</div>

            <div class="flex items-center justify-end gap-3 pt-1">
              <button type="button" class="create-btn-ghost" @click="close">{{ $t('common.cancel') }}</button>
              <button type="submit" :disabled="!form.name.trim() || isSubmitting" class="create-btn-primary">
                <Loader2 v-if="isSubmitting" :size="16" class="animate-spin" aria-hidden="true" />
                <Plus v-else :size="16" aria-hidden="true" />
                <span>{{ isSubmitting ? $t('createModal.creating') : $t('createModal.create') }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <ImageCropperModal
      v-model="showCropper"
      :image-src="cropperImageSrc"
      :aspect-ratio="1"
      :output-size="256"
      @cropped="handleCropped"
    />
  </Teleport>
</template>

<script setup>
import { nextTick, reactive, ref, watch } from 'vue'
import { Image, Loader2, Plus, Upload, X } from 'lucide-vue-next'
import { templatesAPI } from '@/api/templates'
import AppSelect from '@/components/common/AppSelect.vue'
import ImageCropperModal from '@/components/common/ImageCropperModal.vue'
import TemplateIcon from '@/components/common/TemplateIcon.vue'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue', 'created'])
const form = reactive({ name: '', category: 'general', description: '', iconUrl: '' })
const isSubmitting = ref(false)
const errorMessage = ref('')
const fileInputRef = ref(null)
const modalRef = ref(null)
const showCropper = ref(false)
const cropperImageSrc = ref('')
const categoryOptions = [
  { value: 'general', label: 'General' },
  { value: 'automation', label: 'Automation' },
  { value: 'browser', label: 'Browser' },
  { value: 'data', label: 'Data' },
  { value: 'http', label: 'HTTP / API' },
]

watch(() => props.modelValue, async shown => {
  if (!shown) return
  Object.assign(form, { name: '', category: 'general', description: '', iconUrl: '' })
  errorMessage.value = ''
  await nextTick()
  document.getElementById('template-name')?.focus()
})

function close() { emit('update:modelValue', false) }

function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    errorMessage.value = 'Please select an image file.'
    return
  }
  const reader = new FileReader()
  reader.onload = loadEvent => {
    cropperImageSrc.value = loadEvent.target.result
    showCropper.value = true
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function handleCropped(dataUrl) {
  form.iconUrl = dataUrl
  showCropper.value = false
}

async function submit() {
  if (!form.name.trim() || isSubmitting.value) return
  isSubmitting.value = true
  errorMessage.value = ''
  const result = await templatesAPI.createTemplate({
    name: form.name.trim(),
    description: form.description.trim(),
    category: form.category,
    steps: [],
    ui: { sections: [], templateIcon: form.iconUrl || undefined },
  })
  isSubmitting.value = false
  if (!result.ok) {
    errorMessage.value = result.error || 'Unable to create workflow'
    return
  }
  emit('created', result.template)
  close()
}
</script>

<style scoped>
/* ========== Modal Shell ========== */
.create-modal {
  position: relative;
  width: 100%;
  max-width: 480px;
  background: #111827;
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 25px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(139, 92, 246, 0.06);
}

/* ========== Header ========== */
.create-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.create-modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: all 0.15s;
}

.create-modal-close:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.8);
}

/* ========== Body ========== */
.create-modal-body {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ========== Icon Section ========== */
.create-icon-section {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.create-icon-preview {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.create-icon-empty {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px dashed rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.03);
  transition: all 0.2s;
}

.create-upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: all 0.15s;
}

.create-upload-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
}

/* ========== Form Fields ========== */
.create-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.create-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.create-input {
  width: 100%;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
}

.create-input::placeholder {
  color: rgba(255, 255, 255, 0.25);
}

.create-input:focus {
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
  background: rgba(255, 255, 255, 0.06);
}

.create-textarea {
  resize: vertical;
  min-height: 80px;
}

/* ========== Error ========== */
.create-error {
  padding: 10px 14px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.15);
  border-radius: 10px;
  font-size: 13px;
  color: #FCA5A5;
}

/* ========== Buttons ========== */
.create-btn-ghost {
  padding: 9px 18px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.create-btn-ghost:hover {
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.06);
}

.create-btn-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border-radius: 10px;
  border: none;
  background: linear-gradient(135deg, #8B5CF6, #6366F1);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.25);
}

.create-btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #A78BFA, #818CF8);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.35);
  transform: translateY(-1px);
}

.create-btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

/* ========== Transitions ========== */
.modal-enter-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .create-modal {
  animation: scale-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.modal-leave-active {
  transition: opacity 0.15s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.animate-scale-in {
  animation: scale-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
