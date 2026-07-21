<template>
  <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
    <button
      @click="$emit('update:modelValue', null)"
      :class="[
        'flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all duration-200',
        modelValue === null
          ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg shadow-purple-500/25'
          : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
      ]"
    >
      <Grid :size="14" />
      {{ $t('common.all') }}
    </button>
    <button
      v-for="cat in categories"
      :key="cat.name"
      @click="$emit('update:modelValue', cat.name)"
      :class="[
        'flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all duration-200',
        modelValue === cat.name
          ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg shadow-purple-500/25'
          : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
      ]"
    >
      <component :is="cat.icon" :size="14" />
      {{ cat.label }}
    </button>
  </div>
</template>

<script setup>
import { Grid } from 'lucide-vue-next'

defineProps({
  modelValue: {
    type: String,
    default: null
  },
  categories: {
    type: Array,
    default: () => []
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }
</style>
