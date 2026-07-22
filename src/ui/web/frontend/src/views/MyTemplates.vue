<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900" @click="openMenuId = null">
    <WaveHero size="medium">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div>
          <h1 class="text-3xl sm:text-4xl font-bold text-white mb-2">{{ $t('myTemplates.title') }}</h1>
          <p class="text-gray-300">{{ $t('myTemplates.subtitle') }}</p>
        </div>
        <div class="flex items-center gap-3">
          <component :is="MyTemplatesHeroExtension" v-if="MyTemplatesHeroExtension" />
          <button
            class="px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white font-medium rounded-lg transition-all flex items-center gap-2 w-fit"
            type="button"
            @click.stop="triggerImportYAML"
          >
            <FileUp :size="18" />
            {{ $t('myTemplates.importYaml') }}
          </button>
          <input ref="yamlFileInput" type="file" accept=".yaml,.yml" class="hidden" @change="handleImportYAML" />
          <button
            class="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30 flex items-center gap-2 w-fit"
            type="button"
            @click.stop="showCreateModal = true"
          >
            <Plus :size="18" />
            {{ $t('myTemplates.newTemplate') }}
          </button>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-6 mt-8 pt-6 border-t border-white/10">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-purple-400"></div>
          <span class="text-sm text-gray-400">{{ $t('myTemplates.stats.total') }}</span>
          <span class="text-lg font-semibold text-white">{{ templates.length }}</span>
        </div>
        <component
          :is="MyTemplatesStatsExtension"
          v-if="MyTemplatesStatsExtension"
          :templates="templates"
        />
      </div>
    </WaveHero>

    <main class="container px-4 py-6">
      <div class="fm-layout">
        <aside class="fm-sidebar">
          <div class="fm-sidebar-header">
            <span class="fm-sidebar-title">{{ $t('templateFolders.folders', 'Folders') }}</span>
          </div>
          <nav class="fm-folder-list">
            <button class="fm-folder-item fm-folder-active" style="--folder-depth: 0" type="button">
              <span class="fm-folder-tree-glyph" />
              <div class="fm-folder-icon" style="color: #8B5CF6">
                <FolderOpen :size="16" />
              </div>
              <span class="fm-folder-name">{{ $t('templateFolders.allTemplates') }}</span>
              <span class="fm-folder-count">{{ templates.length }}</span>
            </button>
          </nav>
        </aside>

        <section class="fm-content">
          <div class="fm-toolbar">
            <TemplateToolbar
              v-model:search-query="searchQuery"
              v-model:sort-by="sortBy"
              v-model:view-mode="viewMode"
              :selection-mode="false"
              :show-select-button="false"
            />
          </div>

          <TemplateFilters
            :available-tags="availableTags"
            :selected-tags="selectedTags"
            @toggle-tag="toggleTag"
            @clear-tags="selectedTags = []"
          />

          <div v-if="loading" class="fm-loading">
            <Loader2 :size="24" class="animate-spin text-purple-400" />
          </div>
          <div v-else-if="error" class="fm-error">
            <AlertCircle :size="20" />
            <span>{{ error }}</span>
            <button class="fm-retry-btn" type="button" @click="loadTemplates">{{ $t('common.retry', 'Retry') }}</button>
          </div>
          <div v-else-if="pagedTemplates.length === 0" class="fm-empty">
            <FolderOpen :size="48" class="text-gray-600" />
            <p class="text-gray-400">
              {{ searchQuery ? $t('common.noSearchResults') : $t('myTemplates.emptyState') }}
            </p>
            <div class="flex gap-3 mt-4">
              <button class="fm-action-btn fm-action-primary" type="button" @click.stop="showCreateModal = true">
                <Plus :size="16" /> {{ $t('myTemplates.newTemplate') }}
              </button>
              <component :is="MyTemplatesEmptyExtension" v-if="MyTemplatesEmptyExtension" />
            </div>
          </div>

          <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            <TemplateCard
              v-for="item in pagedTemplates"
              :key="item.id"
              :template="item"
              :show-menu="openMenuId === item.id"
              @open="openTemplate"
              @edit="openTemplate"
              @duplicate="duplicateTemplate"
              @run="runTemplate"
              @delete="askDelete"
              @toggle-menu="toggleMenu"
            />
          </div>
          <div v-else class="space-y-2">
            <TemplateListItem
              v-for="item in pagedTemplates"
              :key="item.id"
              :template="item"
              @open="openTemplate"
              @edit="openTemplate"
              @run="runTemplate"
              @delete="askDelete"
            />
          </div>

          <div v-if="filteredTemplates.length > pageSize" class="fm-pagination">
            <button class="fm-page-btn" :disabled="page <= 1" @click="page -= 1">
              <ChevronLeft :size="16" />
            </button>
            <span class="fm-page-info">
              {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, filteredTemplates.length) }}
              / {{ filteredTemplates.length }}
            </span>
            <button class="fm-page-btn" :disabled="page >= pageCount" @click="page += 1">
              <ChevronRight :size="16" />
            </button>
          </div>
        </section>
      </div>
    </main>

    <CreateTemplateModal v-model="showCreateModal" @created="onTemplateCreated" />
    <ConfirmDialog
      :show="Boolean(deleteTarget)"
      :title="$t('myTemplates.deleteDialog.title')"
      :message="$t('myTemplates.deleteDialog.message', { name: deleteTarget?.name || '' })"
      :confirm-text="$t('common.delete')"
      variant="danger"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="deleteTarget = null"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { load as parseYAML } from 'js-yaml'
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  FileUp,
  FolderOpen,
  Loader2,
  Plus,
} from 'lucide-vue-next'
import WaveHero from '@/components/common/WaveHero.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import CreateTemplateModal from '@/components/templates/CreateTemplateModal.vue'
import TemplateCard from '@/components/templates/TemplateCard.vue'
import TemplateFilters from '@/components/templates/TemplateFilters.vue'
import TemplateListItem from '@/components/templates/TemplateListItem.vue'
import TemplateToolbar from '@/components/templates/TemplateToolbar.vue'
import { templatesAPI } from '@/api/templates'
import {
  MyTemplatesEmptyExtension,
  MyTemplatesHeroExtension,
  MyTemplatesStatsExtension,
} from '@edition'

const router = useRouter()
const templates = ref([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')
const sortBy = ref('updated')
const viewMode = ref('grid')
const selectedTags = ref([])
const showCreateModal = ref(false)
const yamlFileInput = ref(null)
const deleteTarget = ref(null)
const deleting = ref(false)
const openMenuId = ref(null)
const page = ref(1)
const pageSize = 24

const availableTags = computed(() => [...new Set(templates.value.flatMap(item => item.tags || []))].sort())
const filteredTemplates = computed(() => {
  const needle = searchQuery.value.trim().toLowerCase()
  const items = templates.value.filter(item => {
    const haystack = [item.name, item.description, item.category, ...(item.tags || [])].filter(Boolean).join(' ').toLowerCase()
    const textMatch = !needle || haystack.includes(needle)
    const tagMatch = !selectedTags.value.length || selectedTags.value.every(tag => (item.tags || []).includes(tag))
    return textMatch && tagMatch
  })
  return [...items].sort((a, b) => {
    if (sortBy.value === 'name') return String(a.name || '').localeCompare(String(b.name || ''))
    const key = sortBy.value === 'created' ? 'createdAt' : 'updatedAt'
    return new Date(b[key] || 0).getTime() - new Date(a[key] || 0).getTime()
  })
})
const pageCount = computed(() => Math.max(1, Math.ceil(filteredTemplates.value.length / pageSize)))
const pagedTemplates = computed(() => filteredTemplates.value.slice((page.value - 1) * pageSize, page.value * pageSize))

watch([searchQuery, sortBy, selectedTags], () => { page.value = 1 }, { deep: true })

async function loadTemplates() {
  loading.value = true
  error.value = ''
  const result = await templatesAPI.listTemplates({ page: 1, pageSize: 500 })
  loading.value = false
  if (!result.ok) {
    error.value = result.error || 'Unable to load workflows'
    return
  }
  templates.value = result.templates
}

function toggleTag(tag) {
  selectedTags.value = selectedTags.value.includes(tag)
    ? selectedTags.value.filter(item => item !== tag)
    : [...selectedTags.value, tag]
}
function toggleMenu(id) { openMenuId.value = openMenuId.value === id ? null : id }
function openTemplate(item) { router.push('/templates/builder/' + item.id) }
function runTemplate(item) { router.push('/templates/builder/' + item.id + '?run=1') }
function askDelete(item) { openMenuId.value = null; deleteTarget.value = item }
function triggerImportYAML() { yamlFileInput.value?.click() }

async function duplicateTemplate(item) {
  openMenuId.value = null
  const result = await templatesAPI.createTemplate({
    ...item,
    id: undefined,
    name: (item.name || 'Untitled workflow') + ' Copy',
    templateName: undefined,
  })
  if (!result.ok) {
    error.value = result.error || 'Unable to duplicate workflow'
    return
  }
  templates.value = [result.template, ...templates.value]
}

async function confirmDelete() {
  if (!deleteTarget.value || deleting.value) return
  deleting.value = true
  const result = await templatesAPI.deleteTemplate(deleteTarget.value.id)
  deleting.value = false
  if (!result.ok) {
    error.value = result.error || 'Unable to delete workflow'
    return
  }
  templates.value = templates.value.filter(item => item.id !== deleteTarget.value.id)
  deleteTarget.value = null
}

function onTemplateCreated(item) {
  templates.value = [item, ...templates.value.filter(existing => existing.id !== item.id)]
  router.push('/templates/builder/' + item.id)
}

async function handleImportYAML(event) {
  const file = event.target.files?.[0]
  if (!file) return
  error.value = ''
  try {
    const document = parseYAML(await file.text()) || {}
    const workflow = document.workflow || document
    const result = await templatesAPI.createTemplate({
      name: workflow.name || file.name.replace(/\.ya?ml$/i, ''),
      description: workflow.description || '',
      category: workflow.category || 'general',
      tags: workflow.tags || [],
      steps: workflow.steps || [],
      ui: workflow.ui || null,
    })
    if (!result.ok) throw new Error(result.error || 'Import failed')
    templates.value = [result.template, ...templates.value]
    openTemplate(result.template)
  } catch (importError) {
    error.value = importError.message || 'Import failed'
  } finally {
    event.target.value = ''
  }
}

onMounted(loadTemplates)
</script>

<style scoped>
/* ========== File Manager Layout ========== */
.fm-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
  min-height: 60vh;
}

@media (max-width: 768px) {
  .fm-layout { grid-template-columns: 1fr; }
  .fm-sidebar { display: none; }
}

.fm-sidebar {
  display: flex;
  flex-direction: column;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 12px;
  overflow: hidden;
  position: sticky;
  top: 80px;
  align-self: start;
  max-height: calc(100vh - 100px);
}

.fm-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.fm-sidebar-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.fm-sidebar-add {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.fm-sidebar-add:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.fm-folder-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.fm-folder-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px 8px calc(10px + (var(--folder-depth, 0) * 16px));
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}

.fm-folder-tree-glyph {
  width: 13px;
  min-width: 13px;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fm-folder-item:hover {
  background: rgba(51, 65, 85, 0.4);
  color: #e2e8f0;
}

.fm-folder-active {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
  color: #e2e8f0;
}

.fm-folder-active .fm-folder-count {
  background: rgba(139, 92, 246, 0.25);
  color: #c4b5fd;
}

.fm-folder-icon { flex-shrink: 0; display: flex; min-width: 16px; }
.fm-folder-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.fm-folder-count {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 10px;
  background: rgba(51, 65, 85, 0.5);
  color: #64748b;
  flex-shrink: 0;
}

.fm-folder-menu {
  display: none;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  flex-shrink: 0;
}

.fm-folder-item:hover .fm-folder-menu { display: flex; }
.fm-folder-menu:hover { background: rgba(51, 65, 85, 0.6); color: #e2e8f0; }

.fm-sidebar-footer {
  padding: 8px;
  border-top: 1px solid rgba(51, 65, 85, 0.5);
}

.fm-manage-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.fm-manage-btn:hover { background: rgba(51, 65, 85, 0.4); color: #94a3b8; }

.fm-content { min-width: 0; }
.fm-toolbar { margin-bottom: 12px; }

.fm-loading, .fm-empty, .fm-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 300px;
  text-align: center;
}

.fm-error {
  color: #f87171;
  gap: 8px;
}

.fm-retry-btn {
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid rgba(248, 113, 113, 0.3);
  background: transparent;
  color: #f87171;
  font-size: 13px;
  cursor: pointer;
}

.fm-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 10px;
  border: 1px solid rgba(51, 65, 85, 0.5);
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.fm-action-btn:hover { border-color: rgba(139, 92, 246, 0.5); color: #e2e8f0; }

.fm-action-primary {
  background: linear-gradient(135deg, #7c3aed, #3b82f6);
  border-color: transparent;
  color: #fff;
}

.fm-action-primary:hover { box-shadow: 0 4px 16px rgba(124, 58, 237, 0.3); }

.fm-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 20px 0;
}

.fm-page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid rgba(51, 65, 85, 0.5);
  background: rgba(15, 23, 42, 0.5);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s;
}

.fm-page-btn:hover:not(:disabled) { border-color: rgba(139, 92, 246, 0.5); color: #e2e8f0; }
.fm-page-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.fm-page-info {
  font-size: 13px;
  color: #64748b;
}

/* ========== PR Dialog ========== */
.fade-enter-active { transition: opacity 0.2s ease; }
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.animate-scale-in {
  animation: scale-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
