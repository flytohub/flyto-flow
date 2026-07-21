<template>
  <div
    class="group relative bg-white dark:bg-gray-800/80 dark:backdrop-blur-sm border border-gray-200 dark:border-gray-700/50 rounded-2xl p-5 cursor-pointer transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/10 hover:border-purple-500/40 hover:-translate-y-0.5"
    :class="selected ? 'ring-2 ring-purple-500 border-purple-500 shadow-lg shadow-purple-500/20' : ''"
    @click="selectable ? $emit('toggle-select', template) : $emit('open', template)"
  >
    <!-- Selection Checkbox -->
    <div
      v-if="selectable"
      class="absolute top-3 left-3 z-10"
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

    <!-- Update Available Badge -->
    <div
      v-if="template.hasUpdate"
      class="absolute top-3 left-3 z-10"
      :title="$t('templateCard.updateAvailable')"
    >
      <span class="flex items-center gap-1 px-2 py-1 bg-blue-600 text-white text-xs rounded-full">
        <RefreshCw :size="12" />
        {{ $t('templateCard.update') }}
      </span>
    </div>

    <!-- Source Status Badge -->
    <div
      v-else-if="template.sourceDeleted || template.sourceUnpublished"
      class="absolute top-3 left-3 z-10"
      :title="template.sourceDeleted ? $t('templateCard.sourceDeleted') : $t('templateCard.sourceUnpublished')"
    >
      <span class="flex items-center gap-1 px-2 py-1 bg-amber-600 text-white text-xs rounded-full">
        <AlertTriangle :size="12" />
        {{ template.sourceDeleted ? $t('templateCard.deleted') : $t('templateCard.unpublished') }}
      </span>
    </div>

    <!-- Source Type Badge (Created / Installed) — top-right, hides on hover when menu shows -->
    <div
      v-if="template._source && !selectable && !template.hasUpdate"
      class="absolute top-3 right-3 z-[5] group-hover:opacity-0 transition-opacity pointer-events-none"
    >
      <span
        v-if="template._source === 'created'"
        class="flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-purple-600/80 text-white backdrop-blur-sm"
      >
        <Pencil :size="10" />
        {{ $t('templateFolders.created') }}
      </span>
      <span
        v-else-if="template._source === 'installed'"
        class="flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-blue-600/80 text-white backdrop-blur-sm"
      >
        <Download :size="10" />
        {{ $t('templateFolders.installed') }}
      </span>
    </div>

    <!-- Quick Actions -->
    <div class="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
      <div class="relative" @click.stop>
        <button
          @click="$emit('toggle-menu', template.id)"
          aria-label="More actions"
          class="p-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
        >
          <MoreVertical :size="16" />
        </button>
        <div
          v-if="showMenu"
          class="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 z-10"
        >
          <button @click="$emit('edit', template)" aria-label="Edit info" class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2">
            <Pencil :size="14" /> {{ $t('templateCard.editInfo') }}
          </button>
          <button @click="$emit('duplicate', template)" aria-label="Save to library" class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2">
            <Copy :size="14" /> {{ $t('common.saveToLibrary') }}
          </button>
          <button @click="$emit('run', template)" aria-label="Execute" class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2">
            <Play :size="14" /> {{ $t('workflow.execute') }}
          </button>

          <!-- Fork button (for purchased templates) -->
          <button
            v-if="canFork"
            @click="$emit('fork', template)"
            aria-label="Fork template"
            class="w-full px-4 py-2 text-left text-sm text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 flex items-center gap-2"
          >
            <GitFork :size="14" /> {{ $t('templateCard.forkTemplate') }}
          </button>

          <!-- Submit PR button (for forked templates) -->
          <button
            v-if="canSubmitPR"
            @click="$emit('submit-pr', template)"
            aria-label="Submit pull request"
            class="w-full px-4 py-2 text-left text-sm text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 flex items-center gap-2"
          >
            <GitPullRequest :size="14" /> {{ $t('templateCollaboration.pullRequests.create') }}
          </button>

          <!-- Sync button (for purchased templates with updates) -->
          <button
            v-if="canSync"
            @click="$emit('sync', template)"
            aria-label="Sync to latest"
            class="w-full px-4 py-2 text-left text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 flex items-center gap-2"
          >
            <RefreshCw :size="14" /> {{ $t('templateCard.syncToLatest') }}
          </button>

          <!-- Auto-update settings (for purchased templates) -->
          <div v-if="canSetAutoUpdate" class="relative">
            <button
              @click.stop="showAutoUpdateMenu = !showAutoUpdateMenu"
              class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between gap-2"
            >
              <span class="flex items-center gap-2">
                <Settings :size="14" /> {{ $t('templateCard.autoUpdate') || 'Auto-update' }}
              </span>
              <span class="text-xs text-gray-400">{{ autoUpdateLabel }}</span>
            </button>
            <!-- Auto-update submenu -->
            <div
              v-if="showAutoUpdateMenu"
              class="absolute left-full top-0 ml-1 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 z-20"
            >
              <button
                v-for="option in autoUpdateOptions"
                :key="option.value"
                @click.stop="setAutoUpdate(option.value)"
                :aria-label="option.label"
                class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between"
                :class="currentAutoUpdate === option.value ? 'text-purple-600 dark:text-purple-400' : 'text-gray-700 dark:text-gray-300'"
              >
                {{ option.label }}
                <Check v-if="currentAutoUpdate === option.value" :size="14" />
              </button>
            </div>
          </div>

          <!-- Move to Folder -->
          <button @click="$emit('move-to-folder', template)" aria-label="Move to folder" class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2">
            <FolderInput :size="14" /> {{ $t('templateFolders.moveToFolder') }}
          </button>

          <!-- Publish Actions (only for created templates) -->
          <template v-if="showPublish">
            <hr class="my-1 border-gray-200 dark:border-gray-700" />
            <button
              @click="$emit('publish', template)"
              aria-label="Publish"
              class="w-full px-4 py-2 text-left text-sm text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 flex items-center gap-2"
            >
              <Rocket :size="14" />
              {{ isPublished ? $t('publish.updatePublishing') : $t('templateCard.publish') }}
            </button>
            <button
              v-if="isPublished && isPrivate"
              @click="$emit('manage-keys', template)"
              aria-label="Manage keys"
              class="w-full px-4 py-2 text-left text-sm text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 flex items-center gap-2"
            >
              <Key :size="14" /> {{ $t('templateCard.manageKeys') }}
            </button>
          </template>

          <hr class="my-1 border-gray-200 dark:border-gray-700" />
          <button @click="$emit('delete', template)" aria-label="Delete" class="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2">
            <Trash2 :size="14" /> {{ $t('common.delete') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Icon -->
    <TemplateIcon
      :icon-url="customIconUrl"
      :color="template.color || template.templateColor"
      :category="template.categorySlug || 'other'"
      size="md"
      :alt="$t('alt.templateIcon')"
      class="mb-3"
    />

    <!-- Content -->
    <h3 class="font-semibold text-gray-900 dark:text-white truncate group-hover:text-purple-400 transition-colors duration-200">
      {{ template.templateName || template.name }}
    </h3>

    <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mt-1.5 min-h-[2.5rem] leading-relaxed">
      {{ template.templateDescription || template.description || 'No description' }}
    </p>

    <!-- Tags -->
    <div v-if="displayTags.length" class="flex flex-wrap gap-1.5 mt-3">
      <span
        v-for="tag in displayTags"
        :key="tag"
        class="px-2 py-0.5 text-[11px] font-medium rounded-md bg-gray-100 dark:bg-gray-700/60 text-gray-500 dark:text-gray-400 transition-colors duration-200 group-hover:dark:text-gray-300"
      >
        #{{ tag }}
      </span>
      <span
        v-if="templateTags.length > 3"
        class="px-2 py-0.5 text-[11px] text-gray-400 dark:text-gray-500"
      >
        +{{ templateTags.length - 3 }}
      </span>
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-between mt-4 pt-3 border-t border-gray-100 dark:border-gray-700/40">
      <div class="flex items-center gap-2 flex-wrap">
        <span
          :class="statusClass"
          class="px-2 py-0.5 rounded-full text-xs font-medium"
        >
          {{ statusLabel }}
        </span>
        <!-- Visibility badge for published templates -->
        <span
          v-if="isPublished && isPrivate"
          class="text-xs text-amber-500 flex items-center gap-1"
          :title="$t('templateCard.privateTooltip')"
        >
          <Lock :size="12" />
        </span>
        <span
          v-else-if="isPublished"
          class="text-xs text-blue-500 flex items-center gap-1"
          :title="$t('templateCard.publicTooltip')"
        >
          <Globe :size="12" />
        </span>
        <span
          v-if="template.source === 'forked'"
          class="text-xs text-gray-400 flex items-center gap-1"
        >
          <GitFork :size="12" /> {{ $t('templateCard.forked') }}
        </span>
        <span
          v-if="template.source === 'purchased'"
          class="text-xs text-emerald-500 flex items-center gap-1"
        >
          <ShoppingCart :size="12" /> {{ $t('templateCard.purchased') }}
        </span>
        <span
          v-if="template.source === 'installed'"
          class="text-xs text-blue-400 flex items-center gap-1"
        >
          <Download :size="12" /> {{ $t('templateCard.installed') }}
        </span>
      </div>
      <span class="text-xs text-gray-400">
        {{ formattedTime }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { MoreVertical, Pencil, Copy, Play, Trash2, GitFork, GitPullRequest, Rocket, Key, Lock, Check, RefreshCw, AlertTriangle, Globe, Settings, ShoppingCart, Download, FolderInput } from 'lucide-vue-next'
import TemplateIcon from '@/components/common/TemplateIcon.vue'
import { useRelativeTime } from '@/composables/useRelativeTime'

const { t } = useI18n()
const { formatRelativeTime } = useRelativeTime()

const props = defineProps({
  template: {
    type: Object,
    required: true
  },
  showMenu: {
    type: Boolean,
    default: false
  },
  showPublish: {
    type: Boolean,
    default: false
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

const emit = defineEmits(['open', 'edit', 'duplicate', 'run', 'delete', 'toggle-menu', 'publish', 'manage-keys', 'toggle-select', 'fork', 'sync', 'update-auto-update', 'submit-pr', 'move-to-folder'])

// Custom icon URL (supports both camelCase and snake_case)
const customIconUrl = computed(() => {
  return props.template.iconUrl || props.template.icon_url || props.template.templateIcon || ''
})

const templateTags = computed(() => {
  return props.template.tags || []
})

const displayTags = computed(() => {
  return templateTags.value.slice(0, 3)
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
  const status = props.template.templateStatus || props.template.status || 'draft'
  return t(`templateCard.status.${status}`, status.charAt(0).toUpperCase() + status.slice(1))
})

const formattedTime = computed(() => {
  return formatRelativeTime(props.template.updatedAt || props.template.createdAt)
})

// Publish status helpers
const isPublished = computed(() => {
  const status = props.template.templateStatus || props.template.status
  return status === 'published'
})

const isPrivate = computed(() => {
  return props.template.visibility === 'private'
})

const hasInviteKey = computed(() => {
  return props.template.hasInviteKey === true
})

// Can fork if:
// 1. Template has a purchase_id (is a purchased template)
// 2. Template is not already a fork
// 3. Source is not deleted
const canFork = computed(() => {
  const hasPurchase = !!props.template.purchaseId || !!props.template.purchaseContext
  const isAlreadyFork = props.template.isFork === true
  const sourceDeleted = props.template.sourceDeleted === true
  return hasPurchase && !isAlreadyFork && !sourceDeleted
})

// Can submit PR if template is a fork and source is not deleted
const canSubmitPR = computed(() => {
  return props.template.isFork === true && !props.template.sourceDeleted
})

// Can sync if:
// 1. Template has a purchase_id (is a purchased template)
// 2. Template has pending update
// 3. Source is not deleted
const canSync = computed(() => {
  const hasPurchase = !!props.template.purchaseId || !!props.template.purchaseContext
  const hasUpdate = props.template.hasUpdate === true
  const sourceDeleted = props.template.sourceDeleted === true
  return hasPurchase && hasUpdate && !sourceDeleted
})

// Auto-update settings
const showAutoUpdateMenu = ref(false)

// Can set auto-update if:
// 1. Template has a purchase_id (is a purchased template)
// 2. Source is not deleted
const canSetAutoUpdate = computed(() => {
  const hasPurchase = !!props.template.purchaseId || !!props.template.purchaseContext
  const sourceDeleted = props.template.sourceDeleted === true
  return hasPurchase && !sourceDeleted
})

// Current auto-update setting
const currentAutoUpdate = computed(() => {
  return props.template.purchaseContext?.autoUpdate || props.template.autoUpdate || 'off'
})

// Auto-update options
const autoUpdateOptions = computed(() => [
  { value: 'off', label: t('templateCard.autoUpdateOff') || 'Off' },
  { value: 'patch', label: t('templateCard.autoUpdatePatch') || 'Patch (x.x.1)' },
  { value: 'minor', label: t('templateCard.autoUpdateMinor') || 'Minor (x.1.x)' },
  { value: 'all', label: t('templateCard.autoUpdateAll') || 'All' }
])

// Auto-update label for display
const autoUpdateLabel = computed(() => {
  const option = autoUpdateOptions.value.find(o => o.value === currentAutoUpdate.value)
  return option ? option.label : 'Off'
})

// Set auto-update policy
function setAutoUpdate(value) {
  showAutoUpdateMenu.value = false
  emit('update-auto-update', props.template, value)
}
</script>
