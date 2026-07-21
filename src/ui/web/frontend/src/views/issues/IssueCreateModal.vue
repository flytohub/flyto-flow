<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="$emit('close')">
      <div class="bg-gray-800/90 backdrop-blur-2xl rounded-2xl border border-white/10 shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <h2 class="text-lg font-bold text-white mb-5">
            {{ $t('issues.newIssue', 'New Issue') }}
          </h2>

          <!-- Title -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-1.5">
              {{ $t('issues.titleLabel', 'Title') }}
            </label>
            <AppInput
              :modelValue="form.title"
              @update:modelValue="$emit('update:form', { ...form, title: $event })"
              :placeholder="$t('issues.titlePlaceholder', 'Brief description of the issue')"
            />
          </div>

          <!-- Type -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-1.5">
              {{ $t('issues.typeLabel', 'Type') }}
            </label>
            <div class="flex gap-2">
              <button
                v-for="t in typeOptions"
                :key="t"
                @click="$emit('update:form', { ...form, type: t })"
                :class="[
                  'flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium transition-all border',
                  form.type === t
                    ? typeActiveClass(t)
                    : 'border-white/10 text-gray-400 hover:border-white/20'
                ]"
              >
                <component :is="typeIcon(t)" :size="14" />
                {{ $t(`issues.type.${t}`, t) }}
              </button>
            </div>
          </div>

          <!-- Priority -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-300 mb-1.5">
              {{ $t('issues.priorityLabel', 'Priority') }}
            </label>
            <div class="flex gap-2">
              <button
                v-for="p in priorityOptions"
                :key="p"
                @click="$emit('update:form', { ...form, priority: p })"
                :class="[
                  'px-3.5 py-2 rounded-xl text-sm font-medium transition-all border',
                  form.priority === p
                    ? priorityActiveClass(p)
                    : 'border-white/10 text-gray-400 hover:border-white/20'
                ]"
              >
                {{ $t(`issues.priority.${p}`, p) }}
              </button>
            </div>
          </div>

          <!-- Description (Markdown) -->
          <div class="mb-4">
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-sm font-medium text-gray-300">
                {{ $t('issues.descriptionLabel', 'Description') }}
              </label>
              <div class="flex items-center bg-gray-900/50 rounded-lg border border-white/10 p-0.5">
                <button
                  @click="previewMode = false"
                  :class="['px-2.5 py-1 text-xs rounded-md transition-colors', !previewMode ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white']"
                >
                  {{ $t('issues.write', 'Write') }}
                </button>
                <button
                  @click="previewMode = true"
                  :class="['px-2.5 py-1 text-xs rounded-md transition-colors', previewMode ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white']"
                >
                  {{ $t('issues.preview', 'Preview') }}
                </button>
              </div>
            </div>
            <AppTextarea
              v-if="!previewMode"
              :modelValue="form.description"
              @update:modelValue="$emit('update:form', { ...form, description: $event })"
              :placeholder="$t('issues.descriptionPlaceholder', 'Describe the issue in detail...')"
              :rows="6"
              @paste="$emit('paste', $event)"
            />
            <div
              v-else
              class="w-full min-h-[156px] px-3 py-2.5 bg-gray-900/50 border border-white/10 rounded-xl text-sm text-gray-300"
            >
              <div v-if="form.description.trim()" class="prose-issue" v-html="renderMarkdown(form.description)"></div>
              <span v-else class="text-gray-500 italic">{{ $t('issues.previewEmpty', 'Nothing to preview') }}</span>
            </div>
            <div class="mt-1 text-xs text-gray-500">
              {{ $t('issues.markdownSupported', 'Markdown supported') }}
            </div>
          </div>

          <!-- Image Upload -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-300 mb-1.5">
              {{ $t('issues.uploadImages', 'Upload Images') }}
            </label>
            <ImageDropzone
              :images="images"
              :uploading="imagesUploading"
              @add="$emit('image-add', $event)"
              @remove="$emit('image-remove', $event)"
            />
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3">
            <button
              @click="$emit('close')"
              class="px-4 py-2 text-sm text-gray-400 hover:text-white border border-white/10 rounded-xl hover:border-white/20 transition-colors"
            >
              {{ $t('common.cancel', 'Cancel') }}
            </button>
            <button
              @click="$emit('submit')"
              :disabled="!form.title.trim() || !form.description.trim() || submitting"
              class="px-5 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-medium rounded-xl hover:shadow-lg hover:shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {{ $t('issues.submit', 'Submit') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { Bug, Lightbulb, HelpCircle, CircleDot } from 'lucide-vue-next'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import AppInput from '@/components/common/AppInput.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'
import ImageDropzone from './ImageDropzone.vue'

defineProps({
  show: { type: Boolean, default: false },
  form: { type: Object, required: true },
  typeOptions: { type: Array, required: true },
  priorityOptions: { type: Array, required: true },
  submitting: { type: Boolean, default: false },
  images: { type: Array, default: () => [] },
  imagesUploading: { type: Boolean, default: false },
})

defineEmits([
  'close',
  'submit',
  'update:form',
  'paste',
  'image-add',
  'image-remove',
])

const previewMode = ref(false)

function renderMarkdown(content) {
  if (!content) return ''
  const html = marked(content)
  return DOMPurify.sanitize(html)
}

function typeIcon(type) {
  switch (type) {
    case 'bug': return Bug
    case 'feature': return Lightbulb
    case 'question': return HelpCircle
    default: return CircleDot
  }
}

function typeActiveClass(type) {
  switch (type) {
    case 'bug': return 'border-red-500/50 bg-red-500/20 text-red-300'
    case 'feature': return 'border-purple-500/50 bg-purple-500/20 text-purple-300'
    case 'question': return 'border-blue-500/50 bg-blue-500/20 text-blue-300'
    default: return 'border-white/20 bg-gray-700 text-gray-300'
  }
}

function priorityActiveClass(priority) {
  switch (priority) {
    case 'high': return 'border-red-500/50 bg-red-500/20 text-red-300'
    case 'medium': return 'border-yellow-500/50 bg-yellow-500/20 text-yellow-300'
    case 'low': return 'border-white/20 bg-gray-700 text-gray-300'
    default: return 'border-white/20 bg-gray-700 text-gray-300'
  }
}
</script>

<style scoped>
/* Markdown prose */
.prose-issue :deep(h1) { font-size: 1.25rem; font-weight: 700; margin: 1rem 0 0.5rem; }
.prose-issue :deep(h2) { font-size: 1.125rem; font-weight: 600; margin: 0.75rem 0 0.5rem; }
.prose-issue :deep(h3) { font-size: 1rem; font-weight: 600; margin: 0.5rem 0 0.25rem; }
.prose-issue :deep(p) { margin: 0.4rem 0; }
.prose-issue :deep(ul), .prose-issue :deep(ol) { padding-left: 1.5rem; margin: 0.4rem 0; }
.prose-issue :deep(ul) { list-style: disc; }
.prose-issue :deep(ol) { list-style: decimal; }
.prose-issue :deep(li) { margin: 0.15rem 0; }
.prose-issue :deep(code) { background: rgba(139,92,246,0.15); padding: 0.15rem 0.4rem; border-radius: 0.25rem; font-size: 0.85em; }
.prose-issue :deep(pre) { background: rgba(0,0,0,0.3); padding: 0.75rem 1rem; border-radius: 0.5rem; overflow-x: auto; margin: 0.5rem 0; }
.prose-issue :deep(pre code) { background: none; padding: 0; }
.prose-issue :deep(blockquote) { border-left: 3px solid rgba(139,92,246,0.4); padding-left: 0.75rem; margin: 0.5rem 0; color: rgb(156,163,175); }
.prose-issue :deep(a) { color: rgb(168,85,247); text-decoration: underline; }
.prose-issue :deep(a:hover) { color: rgb(192,132,252); }
.prose-issue :deep(hr) { border-color: rgba(255,255,255,0.1); margin: 0.75rem 0; }
.prose-issue :deep(table) { width: 100%; border-collapse: collapse; margin: 0.5rem 0; }
.prose-issue :deep(th), .prose-issue :deep(td) { border: 1px solid rgba(255,255,255,0.1); padding: 0.4rem 0.6rem; text-align: left; }
.prose-issue :deep(th) { background: rgba(0,0,0,0.2); font-weight: 600; }
.prose-issue :deep(img) { max-width: 100%; border-radius: 0.5rem; margin: 0.5rem 0; }
</style>
