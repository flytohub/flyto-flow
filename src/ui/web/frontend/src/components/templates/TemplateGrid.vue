<template>
  <!-- Error State -->
  <div v-if="error" class="flex flex-col items-center justify-center py-16">
    <div class="glass-card p-8 max-w-md text-center">
      <div class="empty-state-icon mx-auto mb-6 text-red-400">
        <AlertCircle :size="36" />
      </div>
      <h3 class="text-xl font-semibold text-white mb-3">
        {{ $t('errors.somethingWentWrong') }}
      </h3>
      <p class="text-gray-400 mb-6 leading-relaxed">
        {{ error }}
      </p>
      <button
        @click="$emit('retry')"
        class="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-medium rounded-xl transition-all hover:shadow-lg hover:shadow-purple-500/25 inline-flex items-center justify-center gap-2"
      >
        <RefreshCw :size="18" />
        {{ $t('common.retry') }}
      </button>
    </div>
  </div>

  <!-- Loading Skeleton -->
  <div v-else-if="loading && viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
    <SkeletonCard v-for="i in 8" :key="i" variant="card" />
  </div>
  <div v-else-if="loading && viewMode === 'list'" class="space-y-2">
    <SkeletonCard v-for="i in 6" :key="i" variant="list" />
  </div>

  <!-- Folder Accordion Sections -->
  <div v-else-if="folderSections.length > 0" class="space-y-3">
    <FolderSection
      v-for="section in folderSections"
      :key="section.folder.id"
      :folder="section.folder"
      :templates="section.templates"
      :expanded="expandedFolders.has(section.folder.id)"
      :view-mode="viewMode"
      @toggle="$emit('toggle-folder', $event)"
      @rename="$emit('folder-rename', $event)"
      @delete="$emit('folder-delete', $event)"
    >
      <template #template-card="{ template: tpl }">
        <TemplateCard
          :template="tpl"
          :show-menu="openMenuId === tpl.id"
          :show-publish="tpl._source === 'created'"
          :selectable="selectionMode"
          :selected="selectedIds.has(tpl.id || tpl.templateId)"
          @open="$emit('open', $event)"
          @edit="$emit('edit', $event)"
          @duplicate="$emit('duplicate', $event)"
          @run="$emit('run', $event)"
          @delete="$emit('delete', $event)"
          @toggle-menu="$emit('toggle-menu', $event)"
          @publish="$emit('publish', $event)"
          @manage-keys="$emit('manage-keys', $event)"
          @toggle-select="$emit('toggle-select', $event)"
          @fork="$emit('fork', $event)"
          @sync="$emit('sync', $event)"
          @update-auto-update="$emit('update-auto-update', $event)"
          @submit-pr="$emit('submit-pr', $event)"
          @move-to-folder="$emit('move-to-folder', $event)"
        />
      </template>
      <template #template-list="{ template: tpl }">
        <TemplateListItem
          :template="tpl"
          :selectable="selectionMode"
          :selected="selectedIds.has(tpl.id || tpl.templateId)"
          @open="$emit('open', $event)"
          @edit="$emit('edit', $event)"
          @run="$emit('run', $event)"
          @toggle-menu="$emit('toggle-menu', $event)"
          @toggle-select="$emit('toggle-select', $event)"
          @move-to-folder="$emit('move-to-folder', $event)"
        />
      </template>
    </FolderSection>
  </div>

  <!-- Empty State -->
  <div v-else-if="!loading" class="flex flex-col items-center justify-center py-16">
    <div class="glass-card p-10 max-w-xl w-full text-center relative overflow-hidden border border-purple-500/20">
      <div class="empty-state-icon mx-auto mb-6">
        <Folder :size="36" />
      </div>
      <h3 class="text-xl font-semibold text-white mb-3">
        {{ searchQuery ? $t('myTemplates.empty.noResults') : $t('myTemplates.empty.noTemplates') }}
      </h3>
      <p class="text-gray-400 mb-6 leading-relaxed">
        {{ searchQuery ? $t('myTemplates.empty.tryDifferent') : $t('myTemplates.empty.createFirst') }}
      </p>

      <!-- Quick Actions -->
      <div v-if="!searchQuery" class="space-y-3">
        <button
          @click="$emit('create')"
          class="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-medium rounded-xl transition-all hover:shadow-lg hover:shadow-purple-500/25 inline-flex items-center justify-center gap-2"
        >
          <Plus :size="18" />
          {{ $t('myTemplates.createTemplate') }}
        </button>

        <button
          @click="$emit('browse-marketplace')"
          class="w-full px-6 py-3 bg-transparent border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white font-medium rounded-xl transition-all inline-flex items-center justify-center gap-2"
        >
          <Store :size="18" />
          {{ $t('myTemplates.browseMarketplace') }}
        </button>
      </div>

      <!-- Tips section -->
      <div v-if="!searchQuery" class="mt-8 pt-6 border-t border-gray-700/50">
        <p class="text-xs text-gray-500 mb-3 uppercase tracking-wider">{{ $t('admin.templates.quickTips') }}</p>
        <div class="flex flex-wrap justify-center gap-2">
          <span class="badge badge-primary">{{ $t('admin.templates.dragDropUI') }}</span>
          <span class="badge badge-primary">{{ $t('admin.templates.visualWorkflow') }}</span>
          <span class="badge badge-primary">{{ $t('admin.templates.aiAssistant') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { AlertCircle, RefreshCw, Folder, Plus, Store } from 'lucide-vue-next'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { FolderSection, TemplateCard, TemplateListItem } from '@/components/templates'

defineProps({
  error: { type: String, default: null },
  loading: { type: Boolean, default: false },
  viewMode: { type: String, default: 'grid' },
  folderSections: { type: Array, default: () => [] },
  expandedFolders: { type: Set, default: () => new Set() },
  searchQuery: { type: String, default: '' },
  openMenuId: { type: [String, null], default: null },
  selectionMode: { type: Boolean, default: false },
  selectedIds: { type: Set, default: () => new Set() },
})

defineEmits([
  'retry', 'toggle-folder', 'folder-rename', 'folder-delete',
  'open', 'edit', 'duplicate', 'run', 'delete', 'toggle-menu',
  'publish', 'manage-keys', 'toggle-select', 'fork', 'sync',
  'update-auto-update', 'submit-pr', 'move-to-folder',
  'create', 'browse-marketplace',
])
</script>
