<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Hero Section -->
    <WaveHero size="medium">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div>
          <h1 class="text-3xl sm:text-4xl font-bold text-white mb-2">{{ $t('plugins.title') }}</h1>
          <p class="text-gray-300">{{ $t('plugins.subtitle') }}</p>
        </div>
        <div class="relative">
          <Search :size="18" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <AppInput
            v-model="searchQuery"
            :placeholder="$t('plugins.searchPlaceholder')"
            class="!pl-10"
          />
        </div>
      </div>

      <!-- Stats -->
      <div class="flex flex-wrap items-center gap-6 mt-8 pt-6 border-t border-white/10">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-emerald-400"></div>
          <span class="text-sm text-gray-400">{{ $t('plugins.installed') }}</span>
          <span class="text-lg font-semibold text-emerald-400">{{ installedPlugins.length }}</span>
        </div>
      </div>
    </WaveHero>

    <!-- Main Content -->
    <main class="container px-4 py-6">
      <div class="flex gap-8">
        <!-- Sidebar Categories -->
        <aside class="hidden lg:block w-72 flex-shrink-0">
          <div class="sticky top-6 bg-white dark:bg-gray-800/50 rounded-2xl p-4 border border-gray-200 dark:border-gray-700/50 space-y-2">
            <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
              {{ $t('marketplace.categories') }}
            </h3>

            <!-- Installed -->
            <button
              @click="selectCategory('installed')"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 group',
                selectedCategory === 'installed'
                  ? 'bg-emerald-500/10 text-emerald-500 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-white'
              ]"
            >
              <Box :size="18" :class="['transition-transform duration-200', selectedCategory !== 'installed' && 'group-hover:scale-110']" />
              <span class="flex-1 font-medium">{{ $t('plugins.installedModels') }}</span>
              <span :class="['text-xs px-2 py-0.5 rounded-full', selectedCategory === 'installed' ? 'bg-emerald-500/20' : 'bg-gray-200 dark:bg-gray-700']">
                {{ installedPlugins.length }}
              </span>
            </button>

            <div class="h-px bg-gray-200 dark:bg-gray-700/50 my-2"></div>

            <!-- All -->
            <button
              @click="selectCategory('all')"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 group',
                selectedCategory === 'all'
                  ? 'bg-purple-500/10 text-purple-500 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-white'
              ]"
            >
              <Layers :size="18" :class="['transition-transform duration-200', selectedCategory !== 'all' && 'group-hover:scale-110']" />
              <span class="font-medium">{{ $t('plugins.category.all') }}</span>
            </button>

            <!-- Category List -->
            <button
              v-for="cat in categoryList"
              :key="cat.id"
              @click="selectCategory(cat.id)"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 group',
                selectedCategory === cat.id
                  ? `${cat.bgActive} ${cat.textActive} shadow-sm`
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-white'
              ]"
            >
              <component :is="cat.icon" :size="18" :class="['transition-transform duration-200', selectedCategory !== cat.id && 'group-hover:scale-110']" />
              <span class="font-medium">{{ $t(cat.titleKey) }}</span>
            </button>

            <div class="h-px bg-gray-200 dark:bg-gray-700/50 my-2"></div>

            <!-- Trending -->
            <button
              @click="selectCategory('trending')"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 group',
                selectedCategory === 'trending'
                  ? 'bg-orange-500/10 text-orange-500 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-white'
              ]"
            >
              <Flame :size="18" :class="['transition-transform duration-200', selectedCategory !== 'trending' && 'group-hover:scale-110']" />
              <span class="font-medium">{{ $t('plugins.trending') }}</span>
            </button>
          </div>
        </aside>

        <!-- Plugin Grid -->
        <div class="flex-1">
          <!-- Toolbar -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 mb-6">
            <!-- Mobile category dropdown -->
            <div class="lg:hidden relative" ref="mobileCatRef">
              <button
                @click="mobileCatOpen = !mobileCatOpen"
                class="flex items-center justify-between w-full px-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
                :aria-expanded="mobileCatOpen"
                aria-haspopup="listbox"
              >
                <span>{{ mobileCatLabel }}</span>
                <ChevronDown :size="14" class="text-gray-400 transition-transform" :class="{ 'rotate-180': mobileCatOpen }" />
              </button>
              <Transition name="dropdown">
                <div v-if="mobileCatOpen" class="absolute left-0 right-0 top-full mt-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-black/30 z-50 py-1 overflow-hidden max-h-64 overflow-y-auto" role="listbox">
                  <button
                    v-for="opt in mobileCatOptions"
                    :key="opt.value"
                    @click="selectedCategory = opt.value; mobileCatOpen = false; onCategoryChange()"
                    class="flex items-center justify-between w-full px-3 py-2 text-sm text-left transition-colors"
                    :class="selectedCategory === opt.value
                      ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'"
                    role="option"
                    :aria-selected="selectedCategory === opt.value"
                  >
                    {{ opt.label }}
                    <Check v-if="selectedCategory === opt.value" :size="14" class="text-purple-500" />
                  </button>
                </div>
              </Transition>
            </div>

            <!-- Sort and view toggle -->
            <div class="flex items-center gap-3 ml-auto">
              <!-- Sort dropdown -->
              <div class="relative" ref="sortRef">
                <button
                  @click="sortOpen = !sortOpen"
                  class="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
                  :aria-expanded="sortOpen"
                  aria-haspopup="listbox"
                >
                  <ArrowUpDown :size="14" class="text-gray-400" />
                  <span>{{ sortOptions.find(o => o.value === sortBy)?.label }}</span>
                  <ChevronDown :size="14" class="text-gray-400 transition-transform" :class="{ 'rotate-180': sortOpen }" />
                </button>
                <Transition name="dropdown">
                  <div v-if="sortOpen" class="absolute right-0 top-full mt-1.5 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-black/30 z-50 py-1 overflow-hidden" role="listbox">
                    <button
                      v-for="opt in sortOptions"
                      :key="opt.value"
                      @click="sortBy = opt.value; sortOpen = false"
                      class="flex items-center justify-between w-full px-3 py-2 text-sm text-left transition-colors"
                      :class="sortBy === opt.value
                        ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'"
                      role="option"
                      :aria-selected="sortBy === opt.value"
                    >
                      {{ opt.label }}
                      <Check v-if="sortBy === opt.value" :size="14" class="text-purple-500" />
                    </button>
                  </div>
                </Transition>
              </div>

              <div class="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <button
                  @click="viewMode = 'grid'"
                  :class="viewMode === 'grid' ? 'bg-white dark:bg-gray-700 shadow-sm' : ''"
                  class="p-2 rounded-md transition-colors"
                  aria-label="Grid view"
                >
                  <LayoutGrid :size="18" />
                </button>
                <button
                  @click="viewMode = 'list'"
                  :class="viewMode === 'list' ? 'bg-white dark:bg-gray-700 shadow-sm' : ''"
                  class="p-2 rounded-md transition-colors"
                  aria-label="List view"
                >
                  <List :size="18" />
                </button>
              </div>
            </div>
          </div>

          <!-- Results count -->
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
            {{ displayedPlugins.length }} {{ $t('plugins.models') }}
          </p>

          <!-- Loading State (only show when no results yet) -->
          <div v-if="loading && displayedPlugins.length === 0" class="flex flex-col items-center justify-center py-20">
            <Loader2 :size="40" class="animate-spin text-purple-500 mb-4" />
            <span class="text-gray-400">{{ $t('plugins.loadingModels') }}</span>
          </div>

          <!-- Empty State -->
          <div v-else-if="!loading && displayedPlugins.length === 0" class="text-center py-20">
            <div class="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <Package :size="32" class="text-gray-400" />
            </div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              {{ selectedCategory === 'installed' ? $t('plugins.noInstalled') : $t('plugins.noCategoryResults') }}
            </h3>
            <button
              v-if="selectedCategory === 'installed'"
              @click="selectCategory('all')"
              class="mt-4 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
            >
              {{ $t('plugins.browseModels') }}
            </button>
          </div>

          <!-- Grid View -->
          <div v-else-if="displayedPlugins.length > 0 && viewMode === 'grid'">
            <TransitionGroup
              name="card"
              tag="div"
              class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5"
            >
              <PluginCardNew
                v-for="(plugin, index) in displayedPlugins"
                :key="plugin.modelId"
                :plugin="plugin"
                :installed="isInstalled(plugin.modelId)"
                :show-status="selectedCategory === 'installed'"
                :style="{ '--delay': `${index * 30}ms` }"
                @install="handleInstall"
                @uninstall="handleUninstall"
                @load="handleLoad"
                @unload="handleUnload"
              />
            </TransitionGroup>
          </div>

          <!-- List View -->
          <div v-else-if="displayedPlugins.length > 0" class="space-y-3">
            <div
              v-for="plugin in displayedPlugins"
              :key="plugin.modelId"
              class="flex items-center gap-4 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:shadow-md transition-shadow"
            >
              <!-- Icon -->
              <div :class="['w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0', getCategoryBg(plugin)]">
                <component :is="getCategoryIcon(plugin)" :size="24" class="text-white" />
              </div>

              <!-- Info -->
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-gray-900 dark:text-white truncate">
                  {{ getDisplayName(plugin) }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 truncate">
                  {{ plugin.author || 'Unknown' }} · {{ plugin.task || plugin.pipeline_tag || 'Model' }}
                </p>
              </div>

              <!-- Downloads -->
              <div v-if="plugin.downloads" class="flex items-center gap-1 text-sm text-gray-500">
                <Download :size="14" />
                {{ formatCompactNumber(plugin.downloads) }}
              </div>

              <!-- Actions -->
              <div class="flex items-center gap-2">
                <button
                  v-if="!isInstalled(plugin.modelId)"
                  @click="handleInstall(plugin.modelId)"
                  class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  {{ $t('plugins.install') }}
                </button>
                <template v-else>
                  <span class="px-3 py-1.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-sm rounded-lg flex items-center gap-1">
                    <Check :size="14" />
                    {{ $t('plugins.installed') }}
                  </span>
                  <button
                    @click="handleUninstall(plugin.modelId)"
                    class="p-2 text-gray-400 hover:text-red-500 transition-colors"
                    aria-label="Uninstall"
                  >
                    <Trash2 :size="18" />
                  </button>
                </template>
              </div>
            </div>
          </div>

          <!-- Load More -->
          <div v-if="hasMoreResults && selectedCategory !== 'installed' && displayedPlugins.length > 0" class="flex justify-center mt-8">
            <button
              @click="loadMore"
              :disabled="loadingMore"
              class="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg border border-gray-700 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <Loader2 v-if="loadingMore" :size="18" class="animate-spin" />
              <ChevronDown v-else :size="18" />
              {{ loadingMore ? $t('common.loading') : $t('plugins.loadMore') }}
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Install Progress Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="installProgress.visible"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        >
          <div class="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 class="text-lg font-semibold mb-4 dark:text-white">
              {{ $t('plugins.installing') }}: {{ installProgress.modelId }}
            </h3>
            <div class="mb-4">
              <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-purple-600 transition-all duration-300"
                  :style="{ width: `${installProgress.percent}%` }"
                ></div>
              </div>
              <p class="text-sm text-gray-500 mt-2">
                {{ installProgress.percent.toFixed(0) }}%
              </p>
            </div>
            <p v-if="installProgress.error" class="text-red-500 text-sm">
              {{ installProgress.error }}
            </p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  Search, Loader2, Package, Download, Box, ChevronDown, Check, Trash2,
  Layers, MessageSquare, Cpu, Image, Music, LayoutGrid, List, Flame,
  ArrowUpDown
} from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import AppInput from '@/components/common/AppInput.vue'
import WaveHero from '../components/common/WaveHero.vue'
import PluginCardNew from '../components/plugins/PluginCardNew.vue'
import { useConfirm } from '../composables/useConfirm'
import { useModulesStore, usePluginStore } from '../stores'
import { DEFAULTS } from '@/config/defaults'
import { formatCompactNumber } from '@/utils/format'

const { t, locale } = useI18n()
const modulesStore = useModulesStore()
const pluginStore = usePluginStore()
const confirmDialog = useConfirm()

// Category definitions
const categoryList = [
  {
    id: 'language',
    titleKey: 'plugins.category.language',
    icon: MessageSquare,
    bgActive: 'bg-blue-500/10',
    textActive: 'text-blue-500',
    query: 'llama mistral',
    task: 'text-generation'
  },
  {
    id: 'embedding',
    titleKey: 'plugins.category.embedding',
    icon: Cpu,
    bgActive: 'bg-violet-500/10',
    textActive: 'text-violet-500',
    query: 'embedding sentence-transformers',
    task: 'feature-extraction'
  },
  {
    id: 'vision',
    titleKey: 'plugins.category.vision',
    icon: Image,
    bgActive: 'bg-pink-500/10',
    textActive: 'text-pink-500',
    query: 'vision clip vit',
    task: 'image-classification'
  },
  {
    id: 'audio',
    titleKey: 'plugins.category.audio',
    icon: Music,
    bgActive: 'bg-teal-500/10',
    textActive: 'text-teal-500',
    query: 'whisper audio',
    task: 'automatic-speech-recognition'
  }
]

// State
const searchQuery = ref('')
const selectedCategory = ref('all')
const sortBy = ref('popular')
const viewMode = ref('grid')
const loading = computed(() => pluginStore.isLoading)
const loadingMore = ref(false)
const searchResults = computed(() => pluginStore.searchResults)
const installedPlugins = computed(() => pluginStore.installedPlugins)
const currentPage = ref(0)
const pageSize = DEFAULTS.PAGINATION.PLUGINS
const hasMoreResults = ref(true)
const currentSearchQuery = ref('')
const currentSearchTask = ref('')

// Custom dropdown state
const sortOpen = ref(false)
const sortRef = ref(null)
const mobileCatOpen = ref(false)
const mobileCatRef = ref(null)

const sortOptions = computed(() => [
  { value: 'popular', label: t('plugins.sort.popular', 'Most Popular') },
  { value: 'newest', label: t('plugins.sort.newest', 'Newest') },
  { value: 'name', label: t('plugins.sort.name', 'Name') },
])

const mobileCatOptions = computed(() => [
  { value: 'installed', label: t('plugins.installedModels') },
  { value: 'all', label: t('plugins.category.all') },
  ...categoryList.map(c => ({ value: c.id, label: t(c.titleKey) })),
  { value: 'trending', label: t('plugins.trending') },
])

const mobileCatLabel = computed(() => {
  const opt = mobileCatOptions.value.find(o => o.value === selectedCategory.value)
  return opt?.label || t('plugins.category.all')
})

// Install progress
const installProgress = ref({
  visible: false,
  modelId: '',
  percent: 0,
  error: null
})

// Computed: Displayed plugins based on category
const displayedPlugins = computed(() => {
  if (selectedCategory.value === 'installed') {
    return installedPlugins.value
  }
  return searchResults.value
})

// Helpers
function getDisplayName(plugin) {
  const id = plugin.modelId || plugin.id || ''
  const parts = id.split('/')
  return parts.length > 1 ? parts[1] : id
}

function getCategoryIcon(plugin) {
  const task = plugin.task || plugin.pipeline_tag || ''
  if (task.includes('text-generation') || task.includes('language')) return MessageSquare
  if (task.includes('embedding') || task.includes('feature')) return Cpu
  if (task.includes('image') || task.includes('vision')) return Image
  if (task.includes('audio') || task.includes('speech')) return Music
  return Layers
}

function getCategoryBg(plugin) {
  const task = plugin.task || plugin.pipeline_tag || ''
  if (task.includes('text-generation') || task.includes('language')) return 'bg-gradient-to-br from-blue-500 to-cyan-500'
  if (task.includes('embedding') || task.includes('feature')) return 'bg-gradient-to-br from-purple-500 to-pink-500'
  if (task.includes('image') || task.includes('vision')) return 'bg-gradient-to-br from-orange-500 to-red-500'
  if (task.includes('audio') || task.includes('speech')) return 'bg-gradient-to-br from-green-500 to-emerald-500'
  return 'bg-gradient-to-br from-gray-500 to-gray-600'
}


// Debounced search
let searchTimeout = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    selectedCategory.value = 'all'
    performSearch()
  }, 300)
}

// Select category
function selectCategory(catId) {
  selectedCategory.value = catId
  onCategoryChange()
}

// Handle category change
function onCategoryChange() {
  if (selectedCategory.value === 'installed') {
    loadInstalledPlugins()
    return
  }

  currentPage.value = 0
  pluginStore.clearSearch()

  const cat = categoryList.find(c => c.id === selectedCategory.value)

  if (selectedCategory.value === 'all') {
    performSearch('transformer')
  } else if (selectedCategory.value === 'trending') {
    performSearch('llama', 'text-generation')
  } else if (cat) {
    performSearch(cat.query, cat.task)
  }
}

// Search models
async function performSearch(query = '', task = '') {
  const searchTerm = query || searchQuery.value || 'transformer'

  // Save current search params for pagination
  currentSearchQuery.value = searchTerm
  currentSearchTask.value = task

  const result = await pluginStore.searchModels({
    query: searchTerm,
    task: task || undefined,
    limit: pageSize,
    offset: 0
  })

  if (result.ok) {
    hasMoreResults.value = (result.data?.models || result.data || []).length >= pageSize
  } else {
    hasMoreResults.value = false
  }
}

// Load more results
async function loadMore() {
  if (loadingMore.value || !hasMoreResults.value) return

  loadingMore.value = true
  currentPage.value++

  const offset = currentPage.value * pageSize

  const result = await pluginStore.searchModels({
    query: currentSearchQuery.value,
    task: currentSearchTask.value || undefined,
    limit: pageSize,
    offset: offset,
    append: true
  })

  if (result.ok) {
    const newData = result.data?.models || result.data || []
    hasMoreResults.value = newData.length >= pageSize
  } else {
    hasMoreResults.value = false
  }
  loadingMore.value = false
}

// Load installed plugins
async function loadInstalledPlugins() {
  await pluginStore.fetchInstalled()
}

// Check if model is installed
function isInstalled(modelId) {
  return pluginStore.isInstalled(modelId)
}

// Install model
async function handleInstall(modelId) {
  installProgress.value = {
    visible: true,
    modelId,
    percent: 0,
    error: null
  }

  const progressInterval = setInterval(() => {
    if (installProgress.value.percent < 90) {
      installProgress.value.percent += Math.random() * 15
    }
  }, 500)

  const result = await pluginStore.installModel(modelId)

  clearInterval(progressInterval)

  if (result.ok) {
    installProgress.value.percent = 100
  } else {
    installProgress.value.error = result.error
  }

  setTimeout(() => {
    if (!installProgress.value.error) {
      installProgress.value.visible = false
    }
  }, 1000)
}

// Uninstall model
async function handleUninstall(modelId) {
  const confirmed = await confirmDialog.show({
    title: t('plugins.uninstall'),
    message: t('plugins.confirmUninstall'),
    type: 'warning',
    confirmText: t('plugins.uninstall'),
    cancelText: t('common.cancel')
  })
  if (!confirmed) return

  const result = await pluginStore.uninstallModel(modelId)
  if (result.ok) {
    // Plugin uninstalled successfully
  }
}

// Load/Unload model
async function handleLoad(modelId) {
  await loadInstalledPlugins()
}

async function handleUnload(modelId) {
  await loadInstalledPlugins()
}

// Watch for search query changes
watch(searchQuery, (newVal) => {
  if (!newVal && selectedCategory.value === 'all') {
    performSearch('transformer')
  } else {
    debouncedSearch()
  }
})

function handleClickOutside(e) {
  if (sortRef.value && !sortRef.value.contains(e.target)) {
    sortOpen.value = false
  }
  if (mobileCatRef.value && !mobileCatRef.value.contains(e.target)) {
    mobileCatOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
  loadInstalledPlugins()
  performSearch('transformer')
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})
</script>

<style scoped>
/* Card transition animations */
.card-enter-active {
  transition: all 0.3s ease;
  transition-delay: var(--delay, 0ms);
}

.card-leave-active {
  transition: all 0.2s ease;
}

.card-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.card-leave-to {
  opacity: 0;
}

.card-move {
  transition: transform 0.3s ease;
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease-out;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from > div,
.modal-leave-to > div {
  transform: scale(0.95);
}
</style>
