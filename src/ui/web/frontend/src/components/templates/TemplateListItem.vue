<template>
  <div
    role="button"
    tabindex="0"
    :aria-label="`${template.template_name || template.name}. ${template.template_description || template.description || $t('marketplace.noDescription')}`"
    class="group flex items-center gap-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 cursor-pointer transition-all hover:shadow-md hover:border-purple-300 dark:hover:border-purple-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
    :class="{ 'ring-2 ring-purple-500 border-purple-500': selected }"
    @click="selectable ? $emit('toggle-select', template) : $emit('open', template)"
    @keydown.enter="selectable ? $emit('toggle-select', template) : $emit('open', template)"
    @keydown.space.prevent="selectable ? $emit('toggle-select', template) : $emit('open', template)"
  >
    <!-- Selection Checkbox -->
    <div
      v-if="selectable"
      class="flex-shrink-0"
      @click.stop="$emit('toggle-select', template)"
    >
      <div
        class="w-5 h-5 rounded border-2 flex items-center justify-center transition-all cursor-pointer"
        :class="selected
          ? 'bg-purple-600 border-purple-600'
          : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-500 hover:border-purple-400'"
      >
        <Check v-if="selected" :size="14" class="text-white" />
      </div>
    </div>

    <!-- Icon -->
    <div
      class="w-10 h-10 rounded-lg flex items-center justify-center text-white flex-shrink-0"
      :style="{ background: iconGradient }"
    >
      <component :is="categoryIcon" :size="20" aria-hidden="true" />
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2">
        <h3 class="font-medium text-gray-900 dark:text-white truncate group-hover:text-purple-600 transition-colors">
          {{ template.template_name || template.name }}
        </h3>
        <span
          :class="statusClass"
          class="px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0"
        >
          {{ statusLabel }}
        </span>
        <span
          v-if="template.source === 'forked'"
          class="text-xs text-gray-400 flex items-center gap-1 flex-shrink-0"
        >
          <GitFork :size="12" aria-hidden="true" /> {{ $t('templateCard.forked') }}
        </span>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400 truncate mt-0.5">
        {{ template.template_description || template.description || $t('marketplace.noDescription') }}
      </p>
    </div>

    <!-- Source Badge (right side) -->
    <span
      v-if="template._source === 'created'"
      class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-purple-600/20 text-purple-400 flex-shrink-0 hidden sm:block"
    >
      {{ $t('templateFolders.created') }}
    </span>
    <span
      v-else-if="template._source === 'installed'"
      class="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-blue-600/20 text-blue-400 flex-shrink-0 hidden sm:block"
    >
      {{ $t('templateFolders.installed') }}
    </span>

    <!-- Time -->
    <span class="text-sm text-gray-400 flex-shrink-0 hidden sm:block">
      {{ formattedTime }}
    </span>

    <!-- Actions -->
    <div class="flex items-center gap-1 flex-shrink-0" @click.stop>
      <button
        @click="$emit('run', template)"
        class="p-2 min-w-[44px] min-h-[44px] text-gray-400 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors flex items-center justify-center focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
        :aria-label="$t('common.actions') + ': ' + $t('workflow.execute')"
      >
        <Play :size="18" aria-hidden="true" />
      </button>
      <button
        @click="$emit('edit', template)"
        class="p-2 min-w-[44px] min-h-[44px] text-gray-400 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors flex items-center justify-center focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
        :aria-label="$t('common.edit')"
      >
        <Pencil :size="18" aria-hidden="true" />
      </button>
      <button
        @click="$emit('move-to-folder', template)"
        class="p-2 min-w-[44px] min-h-[44px] text-gray-400 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg transition-colors flex items-center justify-center focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-500"
        :aria-label="$t('templateFolders.moveToFolder')"
      >
        <FolderInput :size="18" aria-hidden="true" />
      </button>
      <button
        @click="$emit('toggle-menu', template.id)"
        class="p-2 min-w-[44px] min-h-[44px] text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-center focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
        :aria-label="$t('common.actions')"
      >
        <MoreVertical :size="18" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Play, Pencil, MoreVertical, GitFork, Folder, Zap, Globe, Database, Bell, Brain, Terminal, ShoppingCart, Share2, Check, FolderInput } from 'lucide-vue-next'

const props = defineProps({
  template: {
    type: Object,
    required: true
  },
  selectable: {
    type: Boolean,
    default: false
  },
  selected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['open', 'edit', 'run', 'toggle-menu', 'toggle-select', 'move-to-folder'])

const categoryIcons = {
  automation: Zap,
  browser: Globe,
  data: Database,
  notification: Bell,
  ai: Brain,
  devops: Terminal,
  ecommerce: ShoppingCart,
  social: Share2
}

const categoryColors = {
  automation: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
  browser: 'linear-gradient(135deg, #3b82f6 0%, #0ea5e9 100%)',
  data: 'linear-gradient(135deg, #10b981 0%, #14b8a6 100%)',
  notification: 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)',
  ai: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
  devops: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
  ecommerce: 'linear-gradient(135deg, #f97316 0%, #ef4444 100%)',
  social: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)'
}

const categoryIcon = computed(() => {
  const slug = props.template.category_slug || 'other'
  return categoryIcons[slug] || Folder
})

const iconGradient = computed(() => {
  const slug = props.template.category_slug || 'other'
  return categoryColors[slug] || 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)'
})

const statusClass = computed(() => {
  const status = props.template.templateStatus || props.template.status
  switch (status) {
    case 'published':
      return 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
    case 'draft':
      return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
    case 'archived':
      return 'bg-gray-100 dark:bg-gray-700 text-gray-500'
    default:
      return 'bg-gray-100 dark:bg-gray-700 text-gray-500'
  }
})

const statusLabel = computed(() => {
  const status = props.template.templateStatus || props.template.status
  return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Draft'
})

const formattedTime = computed(() => {
  const dateStr = props.template.updatedAt || props.template.createdAt
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return 'just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`
  return date.toLocaleDateString()
})
</script>
