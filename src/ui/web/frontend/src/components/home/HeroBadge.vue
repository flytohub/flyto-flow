<template>
  <div class="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 border border-primary-200 rounded-full text-primary-700 text-sm font-semibold dark:(bg-primary-900/30 border-primary-700 text-primary-300)">
    <component :is="icon" v-if="icon" :size="16" />
    <span>{{ text }}</span>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    required: true
  },
  icon: {
    type: [Object, Function],
    default: null
  }
})
</script>
