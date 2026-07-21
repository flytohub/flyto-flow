<template>
  <div v-if="isLoggedIn" class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-4">
    <div class="flex items-center justify-between mb-2">
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
      <span class="text-xs text-gray-500">{{ $t('issues.markdownSupported', 'Markdown supported') }}</span>
    </div>
    <AppTextarea
      v-if="!previewMode"
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :placeholder="$t('issues.commentPlaceholder', 'Leave a comment...')"
      :rows="3"
      @paste="$emit('paste', $event)"
    />
    <div
      v-else
      class="w-full min-h-[80px] px-3 py-2 bg-gray-900/50 border border-white/10 rounded-xl text-sm text-gray-300"
    >
      <div v-if="modelValue.trim()" class="prose-issue" v-html="renderMarkdown(modelValue)"></div>
      <span v-else class="text-gray-500 italic">{{ $t('issues.previewEmpty', 'Nothing to preview') }}</span>
    </div>

    <!-- Comment Image Upload -->
    <ImageDropzone
      :images="images"
      :uploading="imagesUploading"
      @add="$emit('image-add', $event)"
      @remove="$emit('image-remove', $event)"
      class="mt-3"
    />

    <div class="flex justify-end mt-3">
      <button
        @click="$emit('submit')"
        :disabled="(!modelValue.trim() && !images.length) || submitting"
        class="px-5 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-medium rounded-xl hover:shadow-lg hover:shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
      >
        {{ $t('issues.submitComment', 'Comment') }}
      </button>
    </div>
  </div>
  <div v-else class="text-center py-4 text-gray-500 text-sm">
    {{ $t('issues.loginToComment', 'Please log in to comment.') }}
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import AppTextarea from '@/components/common/AppTextarea.vue'
import ImageDropzone from './ImageDropzone.vue'

defineProps({
  modelValue: { type: String, default: '' },
  isLoggedIn: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  images: { type: Array, default: () => [] },
  imagesUploading: { type: Boolean, default: false },
})

defineEmits(['update:modelValue', 'submit', 'paste', 'image-add', 'image-remove'])

const previewMode = ref(false)

function renderMarkdown(content) {
  if (!content) return ''
  const html = marked(content)
  return DOMPurify.sanitize(html)
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
