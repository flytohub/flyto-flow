<template>
  <button
    type="submit"
    :disabled="disabled || loading"
    class="group relative py-4 px-6 border-none rounded-xl text-base font-semibold cursor-pointer overflow-hidden mt-2 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed"
  >
    <span class="btn-bg absolute inset-0 bg-gradient-to-br from-primary-500 to-purple-500 transition-all duration-300"></span>
    <span class="relative flex items-center justify-center gap-2 text-white">
      <Loader2 v-if="loading" :size="20" class="animate-spin" />
      <component :is="icon" v-else-if="icon" :size="20" />
      <slot></slot>
    </span>
  </button>
</template>

<script setup>
import { Loader2 } from 'lucide-vue-next'

defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  icon: {
    type: [Object, Function],
    default: null
  }
})
</script>

<style scoped>
button:hover:not(:disabled) .btn-bg {
  transform: scale(1.02);
  filter: brightness(1.1);
}
</style>
