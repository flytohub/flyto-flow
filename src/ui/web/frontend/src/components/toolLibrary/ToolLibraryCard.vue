<template>
  <div
    class="group bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-5 cursor-pointer transition-all duration-200 hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-lg hover:shadow-primary-500/5 hover:-translate-y-0.5"
    @click="$emit('click')"
  >
    <!-- Header: Icon + Menu -->
    <div class="flex justify-between items-start mb-4">
      <div class="p-2.5 bg-primary-50 dark:bg-primary-900/30 rounded-xl text-primary-600 dark:text-primary-400">
        <component :is="icon" :size="22" />
      </div>
      <div class="relative card-menu">
        <button
          class="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors opacity-0 group-hover:opacity-100"
          @click.stop="$emit('toggle-menu')"
        >
          <MoreVertical :size="16" />
        </button>
        <div
          v-if="showMenu"
          class="absolute top-full right-0 mt-1 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 z-20"
        >
          <button
            class="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click.stop="$emit('edit')"
          >
            <Edit3 :size="14" />
            {{ $t('common.edit') }}
          </button>
          <button
            class="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click.stop="$emit('duplicate')"
          >
            <Copy :size="14" />
            {{ $t('common.duplicate') }}
          </button>
          <button
            class="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            @click.stop="$emit('delete')"
          >
            <Trash2 :size="14" />
            {{ $t('common.delete') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Body -->
    <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1.5 truncate">{{ name }}</h3>
    <p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mb-4 min-h-[2rem]">
      {{ description || $t('toolLibrary.noDescription') }}
    </p>

    <!-- Footer: Category + Steps -->
    <div class="flex items-center gap-3 mb-4">
      <span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-full">
        <component :is="categoryIcon" :size="10" />
        {{ categoryName }}
      </span>
      <span class="inline-flex items-center gap-1 text-[11px] text-gray-400">
        <Layers :size="10" />
        {{ stepsCount }} {{ $t('toolLibrary.steps') }}
      </span>
    </div>

    <!-- Run Button -->
    <button
      class="w-full flex items-center justify-center gap-1.5 py-2 text-sm font-medium text-white bg-emerald-500 hover:bg-emerald-600 rounded-lg transition-colors"
      @click.stop="$emit('run')"
    >
      <Play :size="14" />
      {{ $t('toolLibrary.run') }}
    </button>
  </div>
</template>

<script setup>
import { MoreVertical, Edit3, Copy, Trash2, Layers, Play, Box } from 'lucide-vue-next'

defineProps({
  name: { type: String, default: 'Untitled' },
  description: { type: String, default: '' },
  icon: { type: [Object, Function], default: () => Box },
  categoryIcon: { type: [Object, Function], default: () => Box },
  categoryName: { type: String, default: '' },
  stepsCount: { type: Number, default: 0 },
  showMenu: { type: Boolean, default: false }
})

defineEmits(['click', 'toggle-menu', 'edit', 'duplicate', 'delete', 'run'])
</script>
