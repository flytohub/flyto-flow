<template>
  <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-5">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center">
          <Store :size="16" class="text-white" />
        </div>
        <div>
          <h4 class="font-medium text-white text-sm">{{ $t('publish.showInMarketplace.label') }}</h4>
          <p class="text-xs text-gray-500">
            {{ disabled ? $t('publish.showInMarketplace.disabledDesc') : $t('publish.showInMarketplace.enabledDesc') }}
          </p>
        </div>
      </div>
      <button
        type="button"
        @click="$emit('update:modelValue', !modelValue)"
        :disabled="disabled"
        :class="[
          'relative w-11 h-6 rounded-full transition-all duration-300',
          modelValue && !disabled
            ? 'bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg shadow-purple-500/30'
            : 'bg-slate-700 border border-slate-500',
          disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
        ]"
      >
        <span
          :class="[
            'absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform duration-300 shadow-md',
            modelValue && !disabled ? 'translate-x-5' : 'translate-x-0'
          ]"
        ></span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { Store } from 'lucide-vue-next'

defineProps({
  modelValue: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false }
})

defineEmits(['update:modelValue'])
</script>
