<template>
  <div class="group relative bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-5 hover:border-amber-500/30 transition-all duration-500">
    <div class="flex items-center gap-3 mb-4">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
        <Shield :size="16" class="text-white" />
      </div>
      <h3 class="font-semibold text-white">{{ $t('publish.protection.label') }}</h3>
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
            ? 'bg-amber-500/20 border-amber-500/50 shadow-lg shadow-amber-500/10'
            : 'bg-gray-900/30 border-white/5 hover:border-white/20'
        ]"
      >
        <div class="flex items-center gap-2 mb-1">
          <component
            :is="option.value === 'locked' ? Shield : GitFork"
            :size="14"
            :class="modelValue === option.value ? 'text-amber-400' : 'text-gray-500'"
          />
          <span :class="modelValue === option.value ? 'text-amber-300 font-medium' : 'text-gray-300'">
            {{ option.label }}
          </span>
        </div>
        <p class="text-xs text-gray-500 pl-6">{{ option.description }}</p>
      </button>
    </div>
  </div>
</template>

<script setup>
import { Shield, GitFork } from 'lucide-vue-next'

defineProps({
  modelValue: { type: String, default: 'locked' },
  options: { type: Array, required: true }
})

defineEmits(['update:modelValue'])
</script>
