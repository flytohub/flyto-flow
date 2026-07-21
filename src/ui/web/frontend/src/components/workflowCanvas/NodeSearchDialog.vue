<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isOpen"
        class="node-search-overlay"
        @click.self="close"
        @keydown.escape="close"
      >
        <div class="node-search-dialog" ref="dialogRef">
          <div class="search-header">
            <Search :size="18" class="search-icon" />
            <AppInput
              ref="inputRef"
              v-model="searchQuery"
              :placeholder="safeT('workflowCanvas.search.placeholder', 'Search nodes...')"
              class="search-input"
              @keydown.enter="selectCurrent"
              @keydown.arrow-down.prevent="navigateDown"
              @keydown.arrow-up.prevent="navigateUp"
            />
            <kbd class="search-hint">ESC</kbd>
          </div>

          <div v-if="filteredNodes.length > 0" class="search-results">
            <button
              v-for="(node, index) in filteredNodes"
              :key="node.id"
              class="search-result-item"
              :class="{ active: index === selectedIndex }"
              @click="selectNode(node)"
              @mouseenter="selectedIndex = index"
            >
              <component
                :is="getNodeIcon(node.data?.module)"
                :size="16"
                class="result-icon"
                :style="{ color: getNodeColor(node.data?.module) }"
              />
              <div class="result-content">
                <span class="result-label">{{ resolveModuleLabel(node.data?.module, modulesStore) || node.id }}</span>
                <span class="result-module">{{ node.data?.module }}</span>
              </div>
              <kbd class="result-hint">Enter</kbd>
            </button>
          </div>

          <div v-else-if="searchQuery" class="search-empty">
            {{ safeT('workflowCanvas.search.noResults', 'No nodes found') }}
          </div>

          <div v-else class="search-empty">
            {{ safeT('workflowCanvas.search.hint', 'Type to search for nodes by name or module') }}
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { Search, Box } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import { useNodeStyles } from '@/composables/useNodeStyles'
import { useModulesStore } from '@/stores/modulesStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  nodes: { type: Array, default: () => [] }
})

const emit = defineEmits(['close', 'select'])

const { t, te } = useI18n()

// Helper for safe translation with fallback
const safeT = (key, fallback) => te(key) ? t(key) : fallback
const modulesStore = useModulesStore()
const { getNodeIcon: getIconFromStyles, getCategoryColor } = useNodeStyles()

const inputRef = ref(null)
const dialogRef = ref(null)
const searchQuery = ref('')
const selectedIndex = ref(0)

// Filter nodes based on search query
const filteredNodes = computed(() => {
  if (!searchQuery.value.trim()) return []

  const query = searchQuery.value.toLowerCase()
  return props.nodes
    .filter(node => {
      const label = (resolveModuleLabel(node.data?.module, modulesStore) || '').toLowerCase()
      const module = (node.data?.module || '').toLowerCase()
      const id = node.id.toLowerCase()
      return label.includes(query) || module.includes(query) || id.includes(query)
    })
    .slice(0, 10) // Limit to 10 results
})

// Reset selected index when results change
watch(filteredNodes, () => {
  selectedIndex.value = 0
})

// Focus input when dialog opens
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen) {
    searchQuery.value = ''
    selectedIndex.value = 0
    await nextTick()
    inputRef.value?.focus()
  }
})

function getNodeIcon(moduleId) {
  // Return a default icon component
  return getIconFromStyles(moduleId) || Box
}

function getNodeColor(moduleId) {
  return getCategoryColor(moduleId) || '#8B5CF6'
}

function navigateDown() {
  if (selectedIndex.value < filteredNodes.value.length - 1) {
    selectedIndex.value++
  }
}

function navigateUp() {
  if (selectedIndex.value > 0) {
    selectedIndex.value--
  }
}

function selectCurrent() {
  if (filteredNodes.value.length > 0) {
    selectNode(filteredNodes.value[selectedIndex.value])
  }
}

function selectNode(node) {
  emit('select', node)
  close()
}

function close() {
  emit('close')
}
</script>

<style scoped>
.node-search-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  z-index: 1000;
}

.node-search-dialog {
  background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  width: 480px;
  max-width: 90vw;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(139, 92, 246, 0.15);
  overflow: hidden;
}

.search-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
}

.search-icon {
  color: #8B5CF6;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 16px;
  color: #e2e8f0;
}

.search-input::placeholder {
  color: #64748b;
}

.search-hint {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-family: monospace;
}

.search-results {
  max-height: 320px;
  overflow-y: auto;
  padding: 8px;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.search-result-item:hover,
.search-result-item.active {
  background: rgba(139, 92, 246, 0.15);
}

.search-result-item.active {
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.result-icon {
  flex-shrink: 0;
}

.result-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-label {
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-module {
  color: #64748b;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-hint {
  background: rgba(139, 92, 246, 0.15);
  color: #8B5CF6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-family: monospace;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.search-result-item.active .result-hint {
  opacity: 1;
}

.search-empty {
  padding: 24px;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Scrollbar */
.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: transparent;
}

.search-results::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 3px;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.5);
}
</style>
