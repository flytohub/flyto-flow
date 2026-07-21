<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 backdrop-blur-sm"
      @click.self="$emit('close')"
    >
      <button
        @click="$emit('close')"
        class="absolute top-4 right-4 text-white/60 hover:text-white transition-colors"
      >
        <X :size="24" />
      </button>
      <!-- Nav arrows -->
      <button
        v-if="images.length > 1"
        @click.stop="$emit('prev')"
        class="absolute left-4 text-white/60 hover:text-white transition-colors"
      >
        <ChevronLeft :size="32" />
      </button>
      <button
        v-if="images.length > 1"
        @click.stop="$emit('next')"
        class="absolute right-4 text-white/60 hover:text-white transition-colors"
      >
        <ChevronRight :size="32" />
      </button>
      <img
        :src="images[index]"
        class="max-w-[90vw] max-h-[90vh] object-contain rounded-lg"
      />
      <div v-if="images.length > 1" class="absolute bottom-4 text-white/60 text-sm">
        {{ index + 1 }} / {{ images.length }}
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { X, ChevronLeft, ChevronRight } from 'lucide-vue-next'

defineProps({
  show: { type: Boolean, default: false },
  images: { type: Array, default: () => [] },
  index: { type: Number, default: 0 },
})

defineEmits(['close', 'prev', 'next'])
</script>
