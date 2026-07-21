<template>
  <div class="stat-card text-center p-6 sm:p-8 bg-gray-50 dark:bg-gray-800 rounded-xl">
    <div class="w-16 h-16 mx-auto mb-4 bg-primary-50 rounded-xl flex items-center justify-center text-primary-600 dark:(bg-primary-900/30 text-primary-400)">
      <component :is="icon" :size="32" />
    </div>
    <div
      ref="numberRef"
      class="text-3xl sm:text-4xl font-extrabold text-primary-600 dark:text-primary-400 mb-2"
      :data-target="number"
    >0</div>
    <div class="text-sm sm:text-base text-gray-600 dark:text-gray-400">{{ label }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useScrollAnimation } from '@/composables/useScrollAnimation'

const props = defineProps({
  icon: {
    type: [Object, Function],
    required: true
  },
  number: {
    type: Number,
    required: true
  },
  label: {
    type: String,
    required: true
  }
})

const numberRef = ref(null)
const { observeWithCounter } = useScrollAnimation()

onMounted(() => {
  if (numberRef.value) {
    observeWithCounter(numberRef.value, props.number)
  }
})
</script>
