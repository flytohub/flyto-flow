<template>
  <Transition name="modal">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click="close"
    >
      <!-- Backdrop with blur -->
      <div class="absolute inset-0 bg-black/70 backdrop-blur-md"></div>

      <!-- Ambient glow effects with animation -->
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-[120px] pointer-events-none ambient-glow"></div>
      <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-[120px] pointer-events-none ambient-glow-2"></div>

      <!-- Modal Container -->
      <div
        class="relative bg-gray-900/90 backdrop-blur-xl rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col border border-white/10 overflow-hidden"
        @click.stop
      >
        <!-- Header -->
        <div class="relative p-6 border-b border-white/5">
          <!-- Header glow -->
          <div class="absolute inset-0 bg-gradient-to-r from-purple-500/10 via-transparent to-blue-500/10"></div>

          <div class="relative flex items-center justify-between">
            <div class="flex items-center gap-4">
              <!-- Icon with glow -->
              <div class="relative">
                <div
                  class="absolute inset-0 rounded-xl blur-lg opacity-60"
                  :class="isAddingFirstNode ? 'bg-emerald-500' : 'bg-purple-500'"
                ></div>
                <div
                  class="relative w-12 h-12 rounded-xl flex items-center justify-center"
                  :class="isAddingFirstNode
                    ? 'bg-gradient-to-br from-emerald-400 to-teal-500'
                    : 'bg-gradient-to-br from-purple-400 to-blue-500'"
                >
                  <Play v-if="isAddingFirstNode" :size="22" class="text-white" />
                  <Blocks v-else :size="22" class="text-white" />
                </div>
              </div>

              <div>
                <h2 class="text-xl font-semibold text-white">
                  {{ isAddingFirstNode ? $t('workflow.selectStarterModule', 'Select Starter Module') : $t('workflow.selectModule') }}
                </h2>
                <p class="text-sm text-gray-400 mt-0.5">
                  {{ isAddingFirstNode
                    ? $t('workflow.selectStarterModuleDesc', 'Choose a module to begin your workflow')
                    : $t('workflow.selectModuleDesc')
                  }}
                </p>
              </div>
            </div>

            <button
              @click="close"
              aria-label="Close"
              class="p-2.5 hover:bg-white/10 rounded-xl transition-all text-gray-400 hover:text-white group"
            >
              <X :size="20" class="transition-transform group-hover:rotate-90" />
            </button>
          </div>
        </div>

        <!-- Search & Filters -->
        <div class="p-4 space-y-3 border-b border-white/5 bg-black/20">
          <div class="flex items-center gap-3">
            <!-- Search Input -->
            <div class="relative flex-1 group">
              <div class="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-xl opacity-0 group-focus-within:opacity-100 blur transition-opacity"></div>
              <div class="relative">
                <Search :size="18" class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500 group-focus-within:text-purple-400 transition-colors" />
                <AppInput
                  v-model="searchQuery"
                  :placeholder="$t('workflow.searchModules')"
                  class="!pl-11"
                />
              </div>
            </div>

            <!-- Expert Mode Toggle -->
            <button
              @click="showExpertMode = !showExpertMode"
              :class="[
                'flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all whitespace-nowrap',
                showExpertMode
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/25'
                  : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10 hover:text-white'
              ]"
            >
              <Wrench :size="16" />
              <span>{{ $t('workflow.expertMode') }}</span>
              <ChevronDown
                :size="14"
                :class="['transition-transform duration-300', showExpertMode ? 'rotate-180' : '']"
              />
            </button>
          </div>

          <!-- Category Pills -->
          <div class="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            <button
              @click="selectedCategoryFilter = null"
              :class="[
                'flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all duration-200',
                selectedCategoryFilter === null
                  ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg shadow-purple-500/25'
                  : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
              ]"
            >
              <Grid :size="14" />
              {{ $t('common.all') }}
            </button>
            <button
              v-for="(cat, index) in visibleCategories"
              :key="cat.name"
              @click="selectedCategoryFilter = cat.name"
              :class="[
                'flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all duration-200',
                selectedCategoryFilter === cat.name
                  ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg shadow-purple-500/25'
                  : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
              ]"
              :style="{
                animationDelay: `${index * 30}ms`,
                '--cat-color': getCategoryColor(cat.name)
              }"
            >
              <component :is="cat.icon" :size="14" />
              {{ $te('categories.' + cat.name) ? $t('categories.' + cat.name) : cat.label }}
            </button>
          </div>
        </div>

        <!-- Module List -->
        <div class="flex-1 overflow-y-auto p-4 scrollbar-thin">
          <!-- Loading State -->
          <div v-if="isLoadingModules || isLoadingStarters" class="flex items-center justify-center py-20">
            <div class="flex flex-col items-center gap-4">
              <div class="relative">
                <div class="w-16 h-16 rounded-full border-2 border-purple-500/20"></div>
                <div class="absolute inset-0 w-16 h-16 rounded-full border-2 border-transparent border-t-purple-500 spinner-outer"></div>
                <div class="absolute inset-2 w-12 h-12 rounded-full border-2 border-transparent border-t-blue-500 spinner-inner"></div>
                <div class="absolute inset-0 w-16 h-16 rounded-full bg-purple-500/10 blur-xl"></div>
              </div>
              <p class="text-sm text-gray-400 font-medium">{{ $t('common.loading') }}</p>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else-if="filteredDefaultCategories.length === 0 && filteredExpertCategories.length === 0" class="flex items-center justify-center py-20">
            <div class="flex flex-col items-center gap-4 text-center">
              <div class="w-20 h-20 bg-white/5 rounded-2xl flex items-center justify-center">
                <SearchX :size="36" class="text-gray-500" />
              </div>
              <div>
                <p class="text-base font-medium text-gray-300">{{ $t('workflow.noModulesFound') }}</p>
                <p class="text-sm text-gray-500 mt-1">{{ $t('workflow.tryDifferentSearch') }}</p>
              </div>
            </div>
          </div>

          <!-- Module Content -->
          <div v-else class="space-y-8">
            <!-- Default Modules Section -->
            <div v-if="filteredDefaultCategories.length > 0">
              <div
                v-for="(category, catIndex) in filteredDefaultCategories"
                :key="'default-' + category.name"
                class="mb-8 last:mb-0"
              >
                <!-- Category Header -->
                <div class="flex items-center gap-3 mb-4">
                  <div
                    class="w-8 h-8 rounded-lg flex items-center justify-center"
                    :style="{
                      backgroundColor: getCategoryColor(category.name) + '20',
                      boxShadow: `0 0 20px ${getCategoryColor(category.name)}30`
                    }"
                  >
                    <component :is="category.icon" :size="16" :style="{ color: getCategoryColor(category.name) }" />
                  </div>
                  <span class="text-sm font-semibold text-white">
                    {{ $te('categories.' + category.name) ? $t('categories.' + category.name) : category.label }}
                  </span>
                  <span class="px-2 py-0.5 bg-white/10 text-gray-400 text-xs rounded-md font-medium">
                    {{ category.modules.length }}
                  </span>
                </div>

                <!-- Module Cards Grid with stagger animation -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <TransitionGroup name="card-stagger">
                    <ModuleCard
                      v-for="(module, modIndex) in category.modules"
                      :key="module.module || module.moduleId"
                      :module="module"
                      :style="{ '--stagger-delay': `${(catIndex * 4 + modIndex) * 50}ms` }"
                      class="card-item"
                      @select="selectModule"
                    />
                  </TransitionGroup>
                </div>
              </div>
            </div>

            <!-- Expert Modules Section -->
            <div v-if="showExpertMode && filteredExpertCategories.length > 0">
              <div class="relative flex items-center gap-4 mb-4">
                <div class="flex-1 h-px bg-gradient-to-r from-transparent via-amber-500/30 to-transparent divider-line"></div>
                <div class="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 rounded-lg border border-amber-500/20">
                  <Wrench :size="14" class="text-amber-400" />
                  <span class="text-xs font-semibold text-amber-400">{{ $t('workflow.expertModules') }}</span>
                  <span class="px-1.5 py-0.5 bg-amber-500/20 rounded text-[10px] text-amber-300">
                    {{ expertModuleCount }}
                  </span>
                </div>
                <div class="flex-1 h-px bg-gradient-to-r from-transparent via-amber-500/30 to-transparent divider-line"></div>
              </div>

              <div
                v-for="category in filteredExpertCategories"
                :key="'expert-' + category.name"
                class="mb-6 last:mb-0"
              >
                <div class="flex items-center gap-3 mb-4">
                  <div
                    class="w-8 h-8 rounded-lg flex items-center justify-center"
                    :style="{
                      backgroundColor: getCategoryColor(category.name) + '20',
                      boxShadow: `0 0 20px ${getCategoryColor(category.name)}30`
                    }"
                  >
                    <component :is="category.icon" :size="16" :style="{ color: getCategoryColor(category.name) }" />
                  </div>
                  <span class="text-sm font-semibold text-white">
                    {{ $te('categories.' + category.name) ? $t('categories.' + category.name) : category.label }}
                  </span>
                  <span class="px-2 py-0.5 bg-white/10 text-gray-400 text-xs rounded-md font-medium">
                    {{ category.modules.length }}
                  </span>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <ModuleCard
                    v-for="module in category.modules"
                    :key="module.module || module.moduleId"
                    :module="module"
                    :is-expert="true"
                    @select="selectModule"
                  />
                </div>
              </div>
            </div>

            <!-- Expert Mode Hint (minimal) -->
            <div
              v-if="!showExpertMode && expertModuleCount > 0"
              class="flex items-center justify-center py-4"
            >
              <button
                @click="showExpertMode = true"
                class="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-gray-400 hover:text-white transition-all group"
              >
                <Wrench :size="14" class="text-amber-400" />
                <span>{{ expertModuleCount }} {{ $t('workflow.expertModules') }}</span>
                <ChevronDown :size="14" class="transition-transform group-hover:translate-y-0.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 border-t border-white/5 bg-black/30">
          <div class="flex items-center justify-between text-xs text-gray-500">
            <div class="flex items-center gap-4">
              <span class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-emerald-500 status-pulse"></span>
                {{ totalModuleCount }} {{ $t('workflow.modules', 'modules') }}
              </span>
            </div>
            <div class="flex items-center gap-1.5 text-gray-600">
              <kbd class="px-1.5 py-0.5 bg-white/5 border border-white/10 rounded text-[10px] font-mono text-gray-400">ESC</kbd>
              <span>{{ $t('common.toClose') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, toRef, watch, onMounted, onUnmounted } from 'vue'
import * as LucideIcons from 'lucide-vue-next'
import { X, Search, SearchX, Blocks, Grid, ChevronDown, Wrench, Play } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import ModuleCard from './ModuleCard.vue'
import { useModuleFiltering } from '@/composables/useModuleFiltering'
import { getStarterModules } from '@/api/modules'

const props = defineProps({
  isOpen: Boolean,
  moduleCategories: Array,
  availableSteps: Object,
  isLoadingModules: Boolean,
  defaultModules: {
    type: Array,
    default: () => []
  },
  expertModules: {
    type: Array,
    default: () => []
  },
  isAddingFirstNode: {
    type: Boolean,
    default: false
  },
})

const emit = defineEmits(['close', 'select'])

const starterModuleIds = ref(new Set())
const isLoadingStarters = ref(false)

watch(
  () => props.isOpen && props.isAddingFirstNode,
  async (shouldFetch) => {
    if (shouldFetch) {
      isLoadingStarters.value = true
      try {
        const response = await getStarterModules(true)
        starterModuleIds.value = new Set(
          (response.modules || []).map(m => m.moduleId || m.module_id)
        )
      } catch (err) {
        starterModuleIds.value = null
      } finally {
        isLoadingStarters.value = false
      }
    } else if (!props.isOpen) {
      starterModuleIds.value = new Set()
    }
  },
  { immediate: true }
)

const filteredDefaultModules = computed(() => {
  let modules = props.defaultModules

  // When adding first node, filter to only startable modules
  // Composite/template modules can always start a workflow (self-contained),
  // so only filter atomic modules by starterModuleIds
  if (props.isAddingFirstNode && starterModuleIds.value !== null && starterModuleIds.value.size > 0) {
    modules = modules.filter(m => {
      if (m.source === 'composite' || m.source === 'template' || m.source === 'plugin' || m.category === 'my-templates') {
        return true
      }
      return starterModuleIds.value.has(m.moduleId || m.module_id || m.module)
    })
  }

  return modules
})

const filteredExpertModules = computed(() => {
  if (!props.isAddingFirstNode || starterModuleIds.value === null || starterModuleIds.value.size === 0) {
    return props.expertModules
  }
  return props.expertModules.filter(m => {
    if (m.source === 'composite' || m.source === 'template' || m.source === 'plugin' || m.category === 'my-templates') {
      return true
    }
    return starterModuleIds.value.has(m.moduleId || m.module_id || m.module)
  })
})

const {
  searchQuery,
  selectedCategoryFilter,
  showExpertMode,
  filteredDefaultCategories,
  filteredExpertCategories,
  visibleCategories,
  defaultModuleCount,
  expertModuleCount,
  resetFilters
} = useModuleFiltering({
  defaultModules: filteredDefaultModules,
  expertModules: filteredExpertModules,
})

const totalModuleCount = computed(() => defaultModuleCount.value + expertModuleCount.value)

const categoryColors = {
  browser: '#3B82F6',
  form: '#10B981',
  data: '#F59E0B',
  notification: '#EF4444',
  api: '#8B5CF6',
  file: '#06B6D4',
  composite: '#EC4899',
  developer: '#6366F1',
  string: '#14B8A6',
  array: '#F97316',
  object: '#8B5CF6',
  math: '#EF4444',
  datetime: '#6366F1',
  utility: '#64748B',
  ai: '#A855F7',
  agent: '#A855F7',
  flow: '#10B981',
  http: '#3B82F6',
  element: '#EC4899',
  image: '#F43F5E',
  cloud: '#0EA5E9',
  llm: '#A855F7',
  'my-templates': '#8B5CF6',  // Purple for user templates
  template: '#8B5CF6',
  default: '#6B7280'
}

function getCategoryColor(categoryName) {
  return categoryColors[categoryName] || categoryColors.default
}

function close() {
  resetFilters()
  emit('close')
}

function selectModule(module) {
  emit('select', module)
  close()
}

function handleKeydown(e) {
  if (e.key === 'Escape' && props.isOpen) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
/* Modal transitions */
.modal-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 1, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active > div:nth-child(4),
.modal-leave-active > div:nth-child(4) {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-enter-from > div:nth-child(4) {
  transform: scale(0.9) translateY(40px);
  opacity: 0;
}

.modal-leave-to > div:nth-child(4) {
  transform: scale(0.95) translateY(20px);
  opacity: 0;
}

/* Ambient glow animation */
@keyframes ambientFloat {
  0%, 100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.2;
  }
  50% {
    transform: translate(20px, -20px) scale(1.1);
    opacity: 0.3;
  }
}

.ambient-glow {
  animation: ambientFloat 8s ease-in-out infinite;
}

.ambient-glow-2 {
  animation: ambientFloat 10s ease-in-out infinite reverse;
}

/* Card stagger animation */
.card-item {
  animation: cardSlideIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: var(--stagger-delay, 0ms);
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

@keyframes cardSlideIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Category header animation */
@keyframes headerFadeIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.category-header {
  animation: headerFadeIn 0.4s ease-out forwards;
}

/* Pulse animation for status dot */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.status-pulse {
  animation: pulse 2s ease-in-out infinite;
}

/* Loading spinner */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.spinner-outer {
  animation: spin 1.5s linear infinite;
}

.spinner-inner {
  animation: spin 1s linear infinite reverse;
}

/* Search focus glow */
@keyframes searchGlow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
  }
  50% {
    box-shadow: 0 0 30px rgba(139, 92, 246, 0.5);
  }
}

.search-focused {
  animation: searchGlow 2s ease-in-out infinite;
}

/* Scrollbar */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

.scrollbar-none::-webkit-scrollbar {
  display: none;
}

.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* Section divider animation */
@keyframes lineGrow {
  from {
    transform: scaleX(0);
  }
  to {
    transform: scaleX(1);
  }
}

.divider-line {
  animation: lineGrow 0.6s ease-out forwards;
  transform-origin: center;
}
</style>
