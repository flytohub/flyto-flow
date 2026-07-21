<template>
  <div class="flex relative bg-white/5 rounded-xl p-1 mb-6" role="tablist">
    <button
      v-for="tab in tabs"
      :key="tab.value"
      class="flex-1 flex items-center justify-center gap-2 py-3 px-4 text-[0.9rem] font-semibold bg-transparent border-none rounded-lg cursor-pointer transition-all duration-300 relative z-1 focus-visible:outline-2 focus-visible:outline-purple-500 focus-visible:outline-offset-2"
      :class="modelValue === tab.value ? 'text-white' : 'text-white/50'"
      @click="$emit('update:modelValue', tab.value)"
      role="tab"
      :aria-selected="modelValue === tab.value"
    >
      <component :is="tab.icon" v-if="tab.icon" :size="16" aria-hidden="true" />
      {{ tab.label }}
    </button>
    <div
      class="absolute top-1 left-1 h-[calc(100%-8px)] bg-gradient-to-br from-primary-500 to-purple-500 rounded-lg transition-transform duration-300"
      :style="indicatorStyle"
      aria-hidden="true"
    ></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    required: true
  },
  tabs: {
    type: Array,
    required: true
  }
})

defineEmits(['update:modelValue'])

const indicatorStyle = computed(() => {
  const index = props.tabs.findIndex(t => t.value === props.modelValue)
  const width = 100 / props.tabs.length
  return {
    width: `calc(${width}% - 4px)`,
    transform: `translateX(${index * 100}%)`
  }
})
</script>
