<template>
  <Transition
    enter-active-class="transition-all duration-300 ease-out"
    enter-from-class="translate-y-full opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition-all duration-200 ease-in"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-full opacity-0"
  >
    <div
      v-if="selectedCount > 0"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-3 bg-gray-900 dark:bg-gray-800 border border-gray-700 rounded-xl shadow-2xl"
    >
      <!-- Selection count -->
      <div class="flex items-center gap-2 pr-3 border-r border-gray-700">
        <div class="w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center text-xs font-bold text-white">
          {{ selectedCount }}
        </div>
        <span class="text-sm text-gray-300">{{ $t('batch.selected') }}</span>
      </div>

      <!-- Select All / Deselect All -->
      <button
        v-if="selectedCount < totalCount"
        @click="$emit('select-all')"
        class="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
      >
        <CheckSquare :size="16" />
        {{ $t('batch.selectAll') }}
      </button>
      <button
        v-else
        @click="$emit('deselect-all')"
        class="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
      >
        <Square :size="16" />
        {{ $t('batch.deselectAll') }}
      </button>

      <!-- Batch Delete -->
      <button
        @click="$emit('batch-delete')"
        :disabled="deleting"
        class="flex items-center gap-2 px-3 py-1.5 text-sm text-red-400 hover:text-red-300 hover:bg-red-900/30 rounded-lg transition-colors disabled:opacity-50"
      >
        <Loader2 v-if="deleting" :size="16" class="animate-spin" />
        <Trash2 v-else :size="16" />
        {{ $t('batch.delete') }}
      </button>

      <!-- Cancel -->
      <button
        @click="$emit('cancel')"
        class="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
      >
        <X :size="16" />
        {{ $t('common.cancel') }}
      </button>
    </div>
  </Transition>
</template>

<script setup>
import { CheckSquare, Square, Trash2, X, Loader2 } from 'lucide-vue-next'

defineProps({
  selectedCount: {
    type: Number,
    required: true
  },
  totalCount: {
    type: Number,
    required: true
  },
  deleting: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select-all', 'deselect-all', 'batch-delete', 'cancel'])
</script>
