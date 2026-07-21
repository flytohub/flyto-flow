<template>
  <div class="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-white/[0.02] text-xs">
    <div class="flex items-center gap-1.5 text-gray-400">
      <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
      <span>{{ defaultCount }} {{ $t('workflow.addNode.recommended') }}</span>
      <span v-if="expertCount > 0" class="text-gray-600">
        + {{ expertCount }} {{ $t('workflow.addNode.expert') }}
      </span>
    </div>
    <button
      @click="$emit('toggle-expert')"
      :class="[
        'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all whitespace-nowrap',
        showExpert
          ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25'
          : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10 hover:text-white'
      ]"
    >
      <Wrench :size="14" />
      <span>{{ $t('workflow.expertMode') }}</span>
      <ChevronDown
        :size="14"
        :class="['transition-transform duration-300', showExpert ? 'rotate-180' : '']"
      />
    </button>
  </div>
</template>

<script setup>
import { Wrench, ChevronDown } from 'lucide-vue-next'

defineProps({
  defaultCount: {
    type: Number,
    default: 0
  },
  expertCount: {
    type: Number,
    default: 0
  },
  showExpert: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle-expert'])
</script>
