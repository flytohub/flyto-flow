<template>
  <div class="flex items-center justify-center py-20">
    <div class="flex flex-col items-center gap-4 text-center">
      <div class="w-20 h-20 bg-white/5 rounded-2xl flex items-center justify-center">
        <SearchX :size="36" class="text-gray-500" />
      </div>
      <div>
        <p class="text-base font-medium text-gray-300">{{ $t('workflow.addNode.noResults') }}</p>
        <p class="text-sm text-gray-500 mt-1">{{ $t('workflow.addNode.tryDifferentSearch') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { SearchX } from 'lucide-vue-next'
</script>
