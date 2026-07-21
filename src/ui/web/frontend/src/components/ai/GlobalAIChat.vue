<template>
  <AIChatWindow
    :show="show"
    @close="$emit('close')"
  />
</template>

<script setup>
import { defineAsyncComponent } from 'vue'

const AIChatWindow = defineAsyncComponent(() =>
  import('./AIChatWindow.vue')
)

defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close'])
</script>
