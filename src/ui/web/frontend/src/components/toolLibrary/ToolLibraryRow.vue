<template>
  <div
    class="group flex items-center gap-4 px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl cursor-pointer transition-all duration-200 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-sm"
    @click="$emit('click')"
  >
    <!-- Icon -->
    <div class="p-2 bg-primary-50 dark:bg-primary-900/30 rounded-lg text-primary-600 dark:text-primary-400 flex-shrink-0">
      <component :is="icon" :size="18" />
    </div>

    <!-- Info -->
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{{ name }}</div>
      <div class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ description || $t('toolLibrary.noDescription') }}</div>
    </div>

    <!-- Category -->
    <span class="hidden sm:inline-flex items-center px-2.5 py-0.5 text-[11px] font-medium bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-full flex-shrink-0">
      {{ categoryName }}
    </span>

    <!-- Steps -->
    <span class="hidden sm:inline-flex items-center gap-1 text-xs text-gray-400 flex-shrink-0 w-12">
      <Layers :size="12" />
      {{ stepsCount }}
    </span>

    <!-- Actions -->
    <div class="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
      <button
        class="p-1.5 rounded-lg text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors"
        @click.stop="$emit('run')"
        :title="$t('toolLibrary.run')"
      >
        <Play :size="15" />
      </button>
      <button
        class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        @click.stop="$emit('edit')"
        :title="$t('common.edit')"
      >
        <Edit3 :size="15" />
      </button>
      <button
        class="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
        @click.stop="$emit('delete')"
        :title="$t('common.delete')"
      >
        <Trash2 :size="15" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { Layers, Play, Edit3, Trash2, Box } from 'lucide-vue-next'

defineProps({
  name: { type: String, default: 'Untitled' },
  description: { type: String, default: '' },
  icon: { type: [Object, Function], default: () => Box },
  categoryName: { type: String, default: '' },
  stepsCount: { type: Number, default: 0 }
})

defineEmits(['click', 'run', 'edit', 'delete'])
</script>
