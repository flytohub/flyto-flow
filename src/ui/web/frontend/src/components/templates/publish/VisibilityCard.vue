<template>
  <div class="group relative bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-5 hover:border-blue-500/30 transition-all duration-500">
    <div class="flex items-center gap-3 mb-4">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center">
        <Globe :size="16" class="text-white" />
      </div>
      <h3 class="font-semibold text-white">{{ $t('publish.visibility.label') }}</h3>
    </div>
    <div class="space-y-2">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        @click="$emit('update:modelValue', option.value)"
        :class="[
          'w-full p-3 rounded-xl text-left transition-all duration-300 border',
          modelValue === option.value
            ? 'bg-purple-500/20 border-purple-500/50 shadow-lg shadow-purple-500/10'
            : 'bg-gray-900/30 border-white/5 hover:border-white/20'
        ]"
      >
        <div class="flex items-center gap-2 mb-1">
          <component
            :is="option.value === 'public' ? Globe : Lock"
            :size="14"
            :class="modelValue === option.value ? 'text-purple-400' : 'text-gray-500'"
          />
          <span :class="modelValue === option.value ? 'text-purple-300 font-medium' : 'text-gray-300'">
            {{ option.label }}
          </span>
        </div>
        <p class="text-xs text-gray-500 pl-6">{{ option.description }}</p>
      </button>
    </div>
  </div>
</template>

<script setup>
import { Globe, Lock } from 'lucide-vue-next'

defineProps({
  modelValue: { type: String, default: 'public' },
  options: { type: Array, required: true }
})

defineEmits(['update:modelValue'])
</script>
