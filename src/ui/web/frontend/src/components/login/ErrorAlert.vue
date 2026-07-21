<template>
  <Transition name="shake">
    <div v-if="message" class="flex items-center gap-2 py-3 px-4 bg-red-500/15 border border-red-500/30 rounded-[10px] text-red-300 text-[0.85rem] mb-4">
      <AlertCircle :size="16" />
      <span>{{ message }}</span>
    </div>
  </Transition>
</template>

<script setup>
import { AlertCircle } from 'lucide-vue-next'

defineProps({
  message: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.shake-enter-active {
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}
</style>
