<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Hero Section -->
    <WaveHero size="small" variant="indigo">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="p-2.5 bg-white/10 rounded-xl">
            <Wrench :size="24" class="text-white" />
          </div>
          <div>
            <h1 class="text-2xl sm:text-3xl font-bold text-white">{{ $t('toolLibrary.title') }}</h1>
            <p class="text-sm text-gray-300 mt-1">{{ $t('toolLibrary.subtitle') }}</p>
          </div>
        </div>
        <button
          @click="createNewTool"
          class="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30 flex items-center gap-2 w-fit text-sm"
        >
          <Plus :size="16" />
          {{ $t('toolLibrary.createTool') }}
        </button>
      </div>
    </WaveHero>

    <!-- Content -->
    <main class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 max-w-7xl">
      <!-- Search and Filter Bar -->
      <div class="flex flex-wrap items-center gap-3 mb-6">
        <!-- Search -->
        <div class="relative flex-1 min-w-[240px]">
          <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <AppInput
            v-model="searchQuery"
            :placeholder="$t('toolLibrary.searchPlaceholder')"
            class="!pl-10"
          />
          <button
            v-if="searchQuery"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            @click="searchQuery = ''"
            aria-label="Clear search"
          >
            <X :size="14" />
          </button>
        </div>

        <!-- Category Pills -->
        <div class="flex gap-1.5 overflow-x-auto flex-shrink-0">
          <button
            class="px-3 py-1.5 text-xs font-medium rounded-full border transition-all whitespace-nowrap"
            :class="selectedCategory === null
              ? 'bg-primary-600 text-white border-primary-600'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'"
            @click="selectedCategory = null"
          >
            {{ $t('toolLibrary.allTools') }}
          </button>
          <button
            v-for="cat in categories"
            :key="cat.id"
            class="px-3 py-1.5 text-xs font-medium rounded-full border transition-all whitespace-nowrap flex items-center gap-1.5"
            :class="selectedCategory === cat.id
              ? 'bg-primary-600 text-white border-primary-600'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700'"
            @click="selectedCategory = cat.id"
          >
            <component :is="getCategoryIcon(cat.icon)" :size="12" />
            {{ cat.name }}
          </button>
        </div>

        <!-- View Toggle -->
        <div class="flex border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden flex-shrink-0">
          <button
            class="p-2 transition-colors"
            :class="viewMode === 'grid'
              ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
              : 'bg-white dark:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'"
            @click="viewMode = 'grid'"
            aria-label="Grid view"
          >
            <LayoutGrid :size="16" />
          </button>
          <button
            class="p-2 transition-colors border-l border-gray-200 dark:border-gray-700"
            :class="viewMode === 'list'
              ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
              : 'bg-white dark:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'"
            @click="viewMode = 'list'"
            aria-label="List view"
          >
            <List :size="16" />
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex flex-col items-center justify-center py-20 text-gray-400">
        <Loader :size="28" class="animate-spin mb-3" />
        <span class="text-sm">{{ $t('common.loading') }}</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredTools.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
        <div class="p-4 bg-gray-100 dark:bg-gray-800 rounded-2xl mb-4">
          <Package :size="40" class="text-gray-400" />
        </div>
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{{ $t('toolLibrary.noTools') }}</h2>
        <p class="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-6">{{ $t('toolLibrary.noToolsDesc') }}</p>
        <button
          @click="createNewTool"
          class="px-4 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg transition-all hover:shadow-lg flex items-center gap-2 text-sm"
        >
          <Plus :size="16" />
          {{ $t('toolLibrary.createFirstTool') }}
        </button>
      </div>

      <!-- Grid View -->
      <div v-else-if="viewMode === 'grid'" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <ToolLibraryCard
          v-for="tool in filteredTools"
          :key="tool.id"
          :name="tool.meta?.name || 'Untitled'"
          :description="tool.meta?.description"
          :icon="getToolIcon(tool.meta?.icon)"
          :category-icon="getCategoryIcon(getCategoryById(tool.meta?.category)?.icon)"
          :category-name="getCategoryById(tool.meta?.category)?.name || tool.meta?.category"
          :steps-count="tool.flow?.steps?.length || 0"
          :show-menu="openMenuId === tool.id"
          @click="openTool(tool)"
          @toggle-menu="toggleMenu(tool.id)"
          @edit="editTool(tool)"
          @duplicate="duplicateTool(tool)"
          @delete="confirmDelete(tool)"
          @run="runTool(tool)"
        />
      </div>

      <!-- List View -->
      <div v-else class="space-y-2">
        <ToolLibraryRow
          v-for="tool in filteredTools"
          :key="tool.id"
          :name="tool.meta?.name || 'Untitled'"
          :description="tool.meta?.description"
          :icon="getToolIcon(tool.meta?.icon)"
          :category-name="getCategoryById(tool.meta?.category)?.name || tool.meta?.category"
          :steps-count="tool.flow?.steps?.length || 0"
          @click="openTool(tool)"
          @run="runTool(tool)"
          @edit="editTool(tool)"
          @delete="confirmDelete(tool)"
        />
      </div>
    </main>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="fixed inset-0 z-[9999] flex items-center justify-center p-4" @click="showDeleteModal = false">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
        <div class="relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-6 w-full max-w-sm shadow-xl" @click.stop>
          <div class="flex items-center gap-3 mb-4">
            <div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
              <AlertTriangle :size="20" class="text-red-500" />
            </div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ $t('toolLibrary.deleteConfirm') }}</h3>
          </div>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">{{ $t('toolLibrary.deleteMessage', { name: toolToDelete?.meta?.name }) }}</p>
          <div class="flex justify-end gap-3">
            <button
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              @click="showDeleteModal = false"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              class="px-4 py-2 text-sm font-medium text-white bg-red-500 rounded-lg hover:bg-red-600 transition-colors"
              @click="deleteTool"
            >
              {{ $t('common.delete') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import AppInput from '@/components/common/AppInput.vue'
import { useToolStorage } from '@/composables/useToolStorage'
import WaveHero from '@/components/common/WaveHero.vue'
import { ToolLibraryCard, ToolLibraryRow } from '@/components/toolLibrary'
import {
  Wrench, Plus, Search, X, LayoutGrid, List, Package, Loader,
  AlertTriangle, Image, FileText, Database, Folder, Globe, Zap, Bot, Box
} from 'lucide-vue-next'

const router = useRouter()
const {
  tools,
  categories,
  isLoading,
  initialize,
  removeTool,
  copyTool
} = useToolStorage()

// State
const searchQuery = ref('')
const selectedCategory = ref(null)
const viewMode = ref('grid')
const openMenuId = ref(null)
const showDeleteModal = ref(false)
const toolToDelete = ref(null)

// Computed
const filteredTools = computed(() => {
  let result = tools.value

  if (selectedCategory.value) {
    result = result.filter(t => t.meta?.category === selectedCategory.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t =>
      t.meta?.name?.toLowerCase().includes(q) ||
      t.meta?.description?.toLowerCase().includes(q)
    )
  }

  return result
})

// Methods
function getCategoryIcon(iconName) {
  const iconMap = {
    Image, FileText, Database, Folder, Globe, Zap, Bot, Box
  }
  return iconMap[iconName] || Box
}

function getToolIcon(iconName) {
  return getCategoryIcon(iconName) || Wrench
}

function getCategoryById(categoryId) {
  return categories.value.find(c => c.id === categoryId)
}

function createNewTool() {
  router.push('/templates/builder?tab=moduleLab&new=1')
}

function openTool(tool) {
  router.push(`/tools/${tool.id}/run`)
}

function editTool(tool) {
  router.push(`/templates/builder?tab=moduleLab&tool=${tool.id}`)
  openMenuId.value = null
}

function runTool(tool) {
  router.push(`/tools/${tool.id}/run`)
}

async function duplicateTool(tool) {
  const newName = `${tool.meta?.name || 'Tool'} (Copy)`
  await copyTool(tool.id, newName)
  openMenuId.value = null
}

function confirmDelete(tool) {
  toolToDelete.value = tool
  showDeleteModal.value = true
  openMenuId.value = null
}

async function deleteTool() {
  if (toolToDelete.value) {
    await removeTool(toolToDelete.value.id)
  }
  showDeleteModal.value = false
  toolToDelete.value = null
}

function toggleMenu(toolId) {
  openMenuId.value = openMenuId.value === toolId ? null : toolId
}

function handleClickOutside(e) {
  if (!e.target.closest('.card-menu')) {
    openMenuId.value = null
  }
}

// Lifecycle
onMounted(() => {
  initialize()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
