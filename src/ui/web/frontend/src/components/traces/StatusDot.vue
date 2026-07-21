<template>
  <span class="w-2 h-2 rounded-full flex-shrink-0" :class="dotClass"></span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const dotClass = computed(() => {
  const classes = {
    completed: 'bg-green-400',
    success: 'bg-green-400',
    failed: 'bg-red-400',
    error: 'bg-red-400',
    running: 'bg-blue-400 animate-pulse',
    pending: 'bg-yellow-400'
  }
  return classes[props.status] || 'bg-gray-400'
})
</script>
