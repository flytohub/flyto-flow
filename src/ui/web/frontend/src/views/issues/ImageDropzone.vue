<template>
  <div>
    <!-- Thumbnails -->
    <div v-if="images.length > 0" class="flex flex-wrap gap-2 mb-2">
      <div v-for="(img, idx) in images" :key="idx" class="relative group">
        <img :src="img" class="w-20 h-20 object-cover rounded-lg border border-white/10" />
        <button
          class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          @click.stop="$emit('remove', idx)"
        >
          <X :size="12" class="text-white" />
        </button>
      </div>
    </div>

    <!-- Uploading indicator -->
    <div v-if="uploading" class="flex items-center gap-2 text-xs text-purple-400 mb-2">
      <Loader2 :size="14" class="animate-spin" />
      {{ $t('issues.uploading', 'Uploading...') }}
    </div>

    <!-- Dropzone -->
    <div
      v-if="images.length < 5"
      :class="[
        'border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors',
        dragging
          ? 'border-purple-500/50 bg-purple-500/10'
          : 'border-white/10 hover:border-purple-500/30 hover:bg-gray-900/30'
      ]"
      @click="onClickUpload"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <div class="flex flex-col items-center gap-1">
        <Upload :size="20" class="text-gray-500" />
        <span class="text-xs text-gray-500">
          {{ $t('issues.dragOrPaste', 'Drag, paste, or click to upload') }}
        </span>
        <span class="text-xs text-gray-600">
          {{ $t('issues.maxImages', 'Max {n} images', { n: 5 }) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { X, Loader2, Upload } from 'lucide-vue-next'

defineProps({
  images: { type: Array, default: () => [] },
  uploading: { type: Boolean, default: false },
})

const emit = defineEmits(['add', 'remove'])

const dragging = ref(false)

function onDragOver(e) {
  e.preventDefault()
  dragging.value = true
}

function onDragLeave() {
  dragging.value = false
}

function onDrop(e) {
  e.preventDefault()
  dragging.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))
  if (files.length) emit('add', files)
}

function onClickUpload() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.multiple = true
  input.onchange = () => {
    const files = Array.from(input.files)
    if (files.length) emit('add', files)
  }
  input.click()
}
</script>
