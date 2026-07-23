<template>
  <div
    role="button"
    tabindex="0"
    class="group flex cursor-pointer items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 transition-all hover:border-purple-300 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-purple-600"
    @click="$emit('open', template)"
    @keydown.enter="$emit('open', template)"
    @keydown.space.prevent="$emit('open', template)"
  >
    <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg text-white" :style="{ background: iconGradient }">
      <component :is="categoryIcon" :size="20" aria-hidden="true" />
    </div>
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2">
        <h3 class="truncate font-medium text-gray-900 transition-colors group-hover:text-purple-600 dark:text-white">
          {{ template.templateName || template.name }}
        </h3>
        <span :class="statusClass" class="flex-shrink-0 rounded-full px-2 py-0.5 text-xs font-medium">
          {{ statusLabel }}
        </span>
      </div>
      <p class="mt-0.5 truncate text-sm text-gray-500 dark:text-gray-400">
        {{ template.templateDescription || template.description || $t('common.noDescription', 'No description') }}
      </p>
    </div>
    <span class="hidden flex-shrink-0 text-sm text-gray-400 sm:block">{{ formattedTime }}</span>
    <div class="flex flex-shrink-0 items-center gap-1" @click.stop>
      <button class="template-list-action hover:text-purple-600 dark:hover:bg-purple-900/20" @click="$emit('run', template)">
        <Play :size="18" aria-hidden="true" />
      </button>
      <button class="template-list-action hover:text-purple-600 dark:hover:bg-purple-900/20" @click="$emit('edit', template)">
        <Pencil :size="18" aria-hidden="true" />
      </button>
      <button class="template-list-action hover:text-red-600 dark:hover:bg-red-900/20" @click="$emit('delete', template)">
        <Trash2 :size="18" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Bell, Brain, Database, Folder, Globe, Pencil, Play, Terminal, Trash2, Zap } from 'lucide-vue-next'
import { useRelativeTime } from '@/composables/useRelativeTime'

const props = defineProps({ template: { type: Object, required: true } })
defineEmits(['open', 'edit', 'run', 'delete'])
const { formatRelativeTime } = useRelativeTime()
const { t } = useI18n()

const categoryIcons = { automation: Zap, browser: Globe, data: Database, notification: Bell, ai: Brain, devops: Terminal }
const categoryColors = {
  automation: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
  browser: 'linear-gradient(135deg, #3b82f6 0%, #0ea5e9 100%)',
  data: 'linear-gradient(135deg, #10b981 0%, #14b8a6 100%)',
  notification: 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)',
  ai: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
  devops: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
}
const category = computed(() => props.template.category || 'other')
const categoryIcon = computed(() => categoryIcons[category.value] || Folder)
const iconGradient = computed(() => categoryColors[category.value] || 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)')
const templateStatus = computed(() => props.template.templateStatus || props.template.status || 'draft')
const statusClass = computed(() => {
  if (templateStatus.value === 'published') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
  if (templateStatus.value === 'draft') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
  return 'bg-gray-100 text-gray-500 dark:bg-gray-700'
})
const statusLabel = computed(() => t(`templateCard.status.${templateStatus.value}`))
const formattedTime = computed(() => formatRelativeTime(props.template.updatedAt || props.template.updated_at || props.template.createdAt || props.template.created_at))
</script>

<style scoped>
.template-list-action {
  display: flex;
  min-height: 44px;
  min-width: 44px;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  padding: 0.5rem;
  color: rgb(156 163 175);
  transition: color 0.15s, background-color 0.15s;
}
.template-list-action:hover { background: rgb(249 250 251); }
:global(.dark .template-list-action:hover) { background: rgb(55 65 81); }
</style>
