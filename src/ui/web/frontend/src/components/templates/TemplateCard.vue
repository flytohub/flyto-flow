<template>
  <div
    class="group relative cursor-pointer rounded-2xl border border-gray-200 bg-white p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-purple-500/40 hover:shadow-xl hover:shadow-purple-500/10 dark:border-gray-700/50 dark:bg-gray-800/80 dark:backdrop-blur-sm"
    @click="$emit('open', template)"
  >
    <div class="absolute right-3 top-3 opacity-0 transition-opacity group-hover:opacity-100">
      <div class="relative" @click.stop>
        <button
          class="rounded-lg bg-gray-100 p-1.5 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
          aria-label="More actions"
          @click="$emit('toggle-menu', template.id)"
        >
          <MoreVertical :size="16" />
        </button>
        <div
          v-if="showMenu"
          class="absolute right-0 z-10 mt-1 w-48 rounded-lg border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800"
        >
          <button class="template-menu-item" @click="$emit('edit', template)">
            <Pencil :size="14" /> {{ $t('templateCard.editInfo') }}
          </button>
          <button class="template-menu-item" @click="$emit('duplicate', template)">
            <Copy :size="14" /> {{ $t('common.duplicate', 'Duplicate') }}
          </button>
          <button class="template-menu-item" @click="$emit('run', template)">
            <Play :size="14" /> {{ $t('workflow.execute') }}
          </button>
          <hr class="my-1 border-gray-200 dark:border-gray-700" />
          <button class="template-menu-item text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20" @click="$emit('delete', template)">
            <Trash2 :size="14" /> {{ $t('common.delete') }}
          </button>
        </div>
      </div>
    </div>

    <TemplateIcon
      :icon-url="customIconUrl"
      :color="template.color"
      :category="template.category || 'other'"
      size="md"
      :alt="$t('alt.templateIcon')"
      class="mb-3"
    />

    <h3 class="truncate font-semibold text-gray-900 transition-colors duration-200 group-hover:text-purple-400 dark:text-white">
      {{ template.templateName || template.name }}
    </h3>
    <p class="mt-1.5 line-clamp-2 min-h-[2.5rem] text-sm leading-relaxed text-gray-500 dark:text-gray-400">
      {{ template.templateDescription || template.description || $t('common.noDescription', 'No description') }}
    </p>

    <div v-if="displayTags.length" class="mt-3 flex flex-wrap gap-1.5">
      <span
        v-for="tag in displayTags"
        :key="tag"
        class="rounded-md bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-500 transition-colors duration-200 group-hover:dark:text-gray-300 dark:bg-gray-700/60 dark:text-gray-400"
      >#{{ tag }}</span>
      <span v-if="templateTags.length > 3" class="px-2 py-0.5 text-[11px] text-gray-400 dark:text-gray-500">
        +{{ templateTags.length - 3 }}
      </span>
    </div>

    <div class="mt-4 flex items-center justify-between border-t border-gray-100 pt-3 dark:border-gray-700/40">
      <span :class="statusClass" class="rounded-full px-2 py-0.5 text-xs font-medium">
        {{ statusLabel }}
      </span>
      <span class="text-xs text-gray-400">{{ formattedTime }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Copy, MoreVertical, Pencil, Play, Trash2 } from 'lucide-vue-next'
import TemplateIcon from '@/components/common/TemplateIcon.vue'
import { useRelativeTime } from '@/composables/useRelativeTime'

const { formatRelativeTime } = useRelativeTime()
const { t } = useI18n()
const props = defineProps({
  template: { type: Object, required: true },
  showMenu: { type: Boolean, default: false },
})

defineEmits(['open', 'edit', 'duplicate', 'run', 'delete', 'toggle-menu'])

const customIconUrl = computed(() => props.template.iconUrl || props.template.icon_url || props.template.ui?.templateIcon || '')
const templateTags = computed(() => props.template.tags || [])
const displayTags = computed(() => templateTags.value.slice(0, 3))
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
.template-menu-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  text-align: left;
  font-size: 0.875rem;
  color: rgb(55 65 81);
}
.template-menu-item:hover { background: rgb(243 244 246); }
:global(.dark) .template-menu-item { color: rgb(209 213 219); }
:global(.dark) .template-menu-item:hover { background: rgb(55 65 81); }
</style>
