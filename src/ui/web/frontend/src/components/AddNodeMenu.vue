<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[1000] flex items-center justify-center"
        @click="handleClose"
      >
        <!-- Backdrop with blur -->
        <div class="absolute inset-0 bg-black/70 backdrop-blur-md"></div>

        <!-- Ambient glow effects -->
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-[120px] pointer-events-none ambient-glow"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-[120px] pointer-events-none ambient-glow-2"></div>

        <!-- Modal Container -->
        <div
          class="relative bg-gray-900/90 backdrop-blur-xl rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col border border-white/10 overflow-hidden"
          @click.stop
        >
          <!-- Header -->
          <AddNodeMenuHeader :isInsertionMode="isInsertionMode" :isReplaceMode="isReplaceMode" @close="handleClose" />

          <!-- Filter indicator badge -->
          <div v-if="moduleFilter" class="px-6 pt-2 bg-transparent">
            <span class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-500/20 border border-purple-500/40 rounded-full text-purple-300 text-xs font-medium">
              <component :is="getFilterIcon(moduleFilter)" :size="14" />
              {{ getFilterLabel(moduleFilter) }}
            </span>
          </div>

          <!-- Search & Filters -->
          <div class="p-4 space-y-3 border-b border-white/5 bg-black/20">
            <AddNodeMenuSearch
              ref="searchInputRef"
              v-model="searchQuery"
              @close="handleClose"
            />
            <AddNodeMenuCategoryPills
              v-model="selectedCategory"
              :categories="availableCategories"
            />
          </div>

          <!-- Stats bar with Expert Mode toggle -->
          <AddNodeMenuStatsBar
            :defaultCount="filteredDefaultModules.length"
            :expertCount="filteredExpertModules.length"
            :showExpert="showExpertMode"
            @toggle-expert="showExpertMode = !showExpertMode"
          />

          <!-- Module List -->
          <div class="flex-1 overflow-y-auto p-4 scrollbar-thin">
            <!-- Loading state -->
            <div v-if="isLoading" class="flex items-center justify-center py-20">
              <div class="flex flex-col items-center gap-4">
                <div class="relative">
                  <div class="w-16 h-16 rounded-full border-2 border-purple-500/20"></div>
                  <div class="absolute inset-0 w-16 h-16 rounded-full border-2 border-transparent border-t-purple-500 animate-spin"></div>
                  <div class="absolute inset-2 w-12 h-12 rounded-full border-2 border-transparent border-t-blue-500 animate-spin-reverse"></div>
                  <div class="absolute inset-0 w-16 h-16 rounded-full bg-purple-500/10 blur-xl"></div>
                </div>
                <p class="text-sm text-gray-400 font-medium">Loading compatible modules...</p>
              </div>
            </div>

            <AddNodeMenuEmptyState v-else-if="filteredModules.length === 0" />

            <div v-else class="space-y-8">
              <AddNodeMenuCategorySection
                v-for="(modules, category) in groupedModules"
                :key="category"
                :category="category"
                :modules="modules"
                :show-create-card="category === 'my-templates'"
                @select-module="handleSelectModule"
                @create-template="emit('create-template')"
              />
            </div>
          </div>

          <!-- Footer -->
          <AddNodeMenuFooter />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Cpu, Brain, Wrench } from 'lucide-vue-next'
import {
  AddNodeMenuHeader,
  AddNodeMenuSearch,
  AddNodeMenuCategoryPills,
  AddNodeMenuStatsBar,
  AddNodeMenuCategorySection,
  AddNodeMenuEmptyState,
  AddNodeMenuFooter
} from './addNodeMenu'
import { useModuleCategories } from '../composables/useModuleCategories'

// Helper functions for filter display
function getFilterIcon(filter) {
  switch (filter) {
    case 'ai': case 'model': return Cpu
    case 'memory': return Brain
    case 'tools': return Wrench
    default: return Cpu
  }
}

function getFilterLabel(filter) {
  switch (filter) {
    case 'ai': return 'AI / LLM'
    case 'model': return 'Model'
    case 'memory': return 'Memory'
    case 'tools': return 'Tools'
    default: return filter
  }
}
// Simple utility to group modules by category (no validation logic)
function groupModulesByCategory(modules) {
  if (!Array.isArray(modules)) return {}
  return modules.reduce((groups, module) => {
    const category = module.category || 'other'
    if (!groups[category]) {
      groups[category] = []
    }
    groups[category].push(module)
    return groups
  }, {})
}

const { getAvailableCategories } = useModuleCategories()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  compatibleModules: {
    type: Array,
    default: () => []
  },
  defaultModules: {
    type: Array,
    default: () => []
  },
  expertModules: {
    type: Array,
    default: () => []
  },
  position: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  // Filter for sub-node types (e.g., 'ai.model', 'ai.memory', 'tools')
  moduleFilter: {
    type: String,
    default: null
  },
  // Whether we're inserting a node on an edge (vs. adding a new node)
  isInsertionMode: {
    type: Boolean,
    default: false
  },
  // Whether we're replacing an existing node with a new module
  isReplaceMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'select-module', 'create-template'])

const searchQuery = ref('')
const searchInputRef = ref(null)
const selectedCategory = ref(null)
const showExpertMode = ref(false)

// Auto-enable expert mode when no default modules exist
watch(
  () => [props.defaultModules, props.expertModules],
  ([defaultMods, expertMods]) => {
    if ((!defaultMods || defaultMods.length === 0) && expertMods && expertMods.length > 0) {
      showExpertMode.value = true
    }
  },
  { immediate: true }
)

// Available categories from modules
const availableCategories = computed(() => {
  return getAvailableCategories(props.compatibleModules)
})

// Focus search input when menu opens
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    nextTick(() => {
      searchInputRef.value?.focus()
    })
    selectedCategory.value = null
  } else {
    searchQuery.value = ''
  }
})

// Filtered DEFAULT modules (recommended)
const filteredDefaultModules = computed(() => {
  let modules = props.defaultModules.length > 0 ? props.defaultModules : []
  return filterModules(modules)
})

// Filtered EXPERT modules (advanced)
const filteredExpertModules = computed(() => {
  let modules = props.expertModules.length > 0 ? props.expertModules : []
  return filterModules(modules)
})

// Combined filtered modules for backward compatibility
const filteredModules = computed(() => {
  if (props.defaultModules.length === 0 && props.expertModules.length === 0) {
    return filterModules(props.compatibleModules || [])
  }

  const defaultFiltered = filteredDefaultModules.value
  const expertFiltered = filteredExpertModules.value

  if (showExpertMode.value) {
    return [...defaultFiltered, ...expertFiltered]
  }

  if (defaultFiltered.length === 0) {
    return expertFiltered
  }

  return defaultFiltered
})

// Group filtered modules by category
const groupedModules = computed(() => {
  return groupModulesByCategory(filteredModules.value)
})

function filterModules(modules) {
  let result = modules

  // Apply moduleFilter from AI Agent sub-node ports
  if (props.moduleFilter) {
    const filter = props.moduleFilter.toLowerCase()
    result = result.filter(module => {
      const moduleId = (module.moduleId || module.module || '').toLowerCase()
      if (filter === 'ai') return module.isAIModel === true
      if (filter === 'model') return moduleId === 'ai.model'
      if (filter === 'memory') return moduleId === 'ai.memory'
      if (filter === 'tools') return module.isTool === true
      return moduleId.startsWith(filter)
    })
  }

  if (selectedCategory.value) {
    result = result.filter(module => {
      const cat = module.category || module.moduleId?.split('.')[0]
      return cat === selectedCategory.value
    })
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(module => {
      return (
        module.label?.toLowerCase().includes(query) ||
        module.description?.toLowerCase().includes(query) ||
        module.moduleId?.toLowerCase().includes(query) ||
        module.module?.toLowerCase().includes(query)
      )
    })
  }

  return result
}

function handleClose() {
  emit('close')
}

function handleSelectModule(module) {
  emit('select-module', module)
}
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
.modal-enter-active > div:last-child,
.modal-leave-active > div:last-child {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-enter-from > div:last-child {
  transform: scale(0.9) translateY(40px);
  opacity: 0;
}
.modal-leave-to > div:last-child {
  transform: scale(0.95) translateY(20px);
  opacity: 0;
}

/* Ambient glow */
@keyframes ambientFloat {
  0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.2; }
  50% { transform: translate(20px, -20px) scale(1.1); opacity: 0.3; }
}
.ambient-glow { animation: ambientFloat 8s ease-in-out infinite; }
.ambient-glow-2 { animation: ambientFloat 10s ease-in-out infinite reverse; }

/* Reverse spin for loader */
@keyframes spin-reverse {
  to { transform: rotate(-360deg); }
}
.animate-spin-reverse { animation: spin-reverse 1s linear infinite; }

/* Scrollbar */
.scrollbar-thin::-webkit-scrollbar { width: 6px; }
.scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
.scrollbar-thin::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
.scrollbar-thin::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>
