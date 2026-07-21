<template>
  <div class="vector-store-params">
    <!-- Operation Mode Tabs -->
    <div class="operation-tabs">
      <button
        v-for="op in operations"
        :key="op.id"
        type="button"
        class="operation-tab"
        :class="{ active: localParams.operation === op.id }"
        @click="setOperation(op.id)"
      >
        <component :is="op.icon" :size="14" />
        <span>{{ $t(op.labelKey) }}</span>
      </button>
    </div>

    <!-- Collection Selector -->
    <div class="param-group">
      <label class="param-label">
        <Database :size="14" />
        {{ $t('vectorStore.collection') }}
        <button
          type="button"
          class="refresh-btn"
          :title="$t('vectorStore.refreshCollections')"
          @click="loadCollections"
          :disabled="loadingCollections"
        >
          <RefreshCw :size="12" :class="{ spinning: loadingCollections }" />
        </button>
      </label>
      <AppSelect
        v-model="localParams.collection"
        :placeholder="$t('vectorStore.selectCollection')"
        :options="collections.map(col => ({ value: col.name, label: col.name + ' (' + col.count + ' docs)' }))"
      />
      <button
        type="button"
        class="create-collection-btn"
        @click="showCreateModal = true"
      >
        <Plus :size="12" />
        {{ $t('vectorStore.createCollection') }}
      </button>
    </div>

    <!-- INSERT MODE -->
    <template v-if="localParams.operation === 'insert'">
      <!-- Document Content -->
      <div class="param-group">
        <PromptTemplateEditor
          v-model="localParams.content"
          :label="$t('vectorStore.content')"
          :placeholder="$t('vectorStore.contentPlaceholder')"
          :rows="4"
          :required="true"
        />
      </div>

      <!-- Document ID (optional) -->
      <div class="param-group">
        <label class="param-label">
          <Hash :size="14" />
          {{ $t('vectorStore.documentId') }}
        </label>
        <AppInput
          v-model="localParams.documentId"
          placeholder="auto-generated if empty"
          size="sm"
        />
      </div>

      <!-- Metadata -->
      <div class="param-group">
        <label class="param-label">
          <Tags :size="14" />
          {{ $t('vectorStore.metadata') }}
        </label>
        <KeyValueEditor
          v-model="localParams.metadata"
          :key-label="'Key'"
          :value-label="'Value'"
          :add-text="$t('vectorStore.addMetadata')"
          :empty-text="$t('vectorStore.noMetadata')"
        />
      </div>
    </template>

    <!-- SEARCH MODE -->
    <template v-if="localParams.operation === 'search'">
      <!-- Query -->
      <div class="param-group">
        <PromptTemplateEditor
          v-model="localParams.query"
          :label="$t('vectorStore.query')"
          :placeholder="$t('vectorStore.queryPlaceholder')"
          :rows="3"
          :required="true"
        />
      </div>

      <!-- Top K -->
      <div class="param-group">
        <label class="param-label">
          <ListOrdered :size="14" />
          {{ $t('vectorStore.topK') }}
          <span class="param-value">{{ localParams.topK }}</span>
        </label>
        <input
          v-model.number="localParams.topK"
          type="range"
          min="1"
          max="20"
          step="1"
          class="param-slider"
        />
      </div>

      <!-- Score Threshold -->
      <div class="param-group">
        <label class="param-label">
          <Gauge :size="14" />
          {{ $t('vectorStore.scoreThreshold') }}
          <span class="param-value">{{ localParams.scoreThreshold.toFixed(2) }}</span>
        </label>
        <input
          v-model.number="localParams.scoreThreshold"
          type="range"
          min="0"
          max="1"
          step="0.05"
          class="param-slider"
        />
        <p class="param-hint">{{ $t('vectorStore.scoreThresholdHint') }}</p>
      </div>

      <!-- Metadata Filters (Collapsible) -->
      <div class="advanced-section">
        <button
          type="button"
          class="advanced-toggle"
          @click="showFilters = !showFilters"
        >
          <ChevronRight :size="14" :class="{ rotated: showFilters }" />
          <span>{{ $t('vectorStore.filters') }}</span>
        </button>

        <Transition name="collapse">
          <div v-if="showFilters" class="advanced-content">
            <KeyValueEditor
              v-model="localParams.filters"
              :key-label="'Field'"
              :value-label="'Value'"
              :add-text="$t('vectorStore.addMetadata')"
              :empty-text="'No filters'"
            />
          </div>
        </Transition>
      </div>
    </template>

    <!-- DELETE MODE -->
    <template v-if="localParams.operation === 'delete'">
      <!-- Delete by IDs -->
      <div class="param-group">
        <label class="param-label">
          <Hash :size="14" />
          {{ $t('vectorStore.deleteIds') }}
        </label>
        <AppTextarea
          v-model="deleteIdsText"
          :placeholder="'Enter document IDs, one per line...'"
          :rows="4"
          size="sm"
        />
        <p class="param-hint">Enter one document ID per line</p>
      </div>
    </template>

    <!-- Create Collection Modal -->
    <Teleport to="body">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>{{ $t('vectorStore.createCollection') }}</h3>
            <button class="modal-close" @click="showCreateModal = false">
              <X :size="18" />
            </button>
          </div>
          <div class="modal-body">
            <label class="param-label">{{ $t('vectorStore.collectionName') }}</label>
            <AppInput
              v-model="newCollectionName"
              placeholder="my_collection"
              @keydown.enter="createCollection"
              size="sm"
            />
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showCreateModal = false">
              {{ $t('common.cancel') }}
            </button>
            <button
              class="btn-primary"
              @click="createCollection"
              :disabled="!newCollectionName.trim() || creatingCollection"
            >
              {{ creatingCollection ? $t('common.creating') : $t('common.create') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, onMounted, markRaw } from 'vue'
import {
  Database,
  ChevronRight,
  RefreshCw,
  Plus,
  Hash,
  Tags,
  ListOrdered,
  Gauge,
  X,
  Download,
  Search,
  Trash2
} from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'
import PromptTemplateEditor from './shared/PromptTemplateEditor.vue'
import KeyValueEditor from './shared/KeyValueEditor.vue'
import { useVectorStore } from '@/composables/useVectorStore'

const props = defineProps({
  params: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:params'])

// Use vector store composable for API calls (zero coupling)
const {
  collections,
  loading: loadingCollections,
  loadCollections: fetchCollections,
  createCollection: createCollectionApi
} = useVectorStore()

// Operation definitions
const operations = [
  { id: 'insert', labelKey: 'vectorStore.operations.insert', icon: markRaw(Download) },
  { id: 'search', labelKey: 'vectorStore.operations.search', icon: markRaw(Search) },
  { id: 'delete', labelKey: 'vectorStore.operations.delete', icon: markRaw(Trash2) }
]

// UI state
const showFilters = ref(false)
const showCreateModal = ref(false)
const newCollectionName = ref('')
const creatingCollection = ref(false)

// Local reactive copy of params
const localParams = reactive({
  operation: props.params.operation || 'search',
  collection: props.params.collection || 'flyto_knowledge',
  content: props.params.content || '',
  documentId: props.params.documentId || '',
  metadata: props.params.metadata || {},
  query: props.params.query || '',
  topK: props.params.topK ?? 5,
  scoreThreshold: props.params.scoreThreshold ?? 0.7,
  filters: props.params.filters || {},
  deleteIds: props.params.deleteIds || [],
  deleteFilter: props.params.deleteFilter || {}
})

// Delete IDs as text (one per line)
const deleteIdsText = computed({
  get: () => localParams.deleteIds.join('\n'),
  set: (val) => {
    localParams.deleteIds = val.split('\n').map(id => id.trim()).filter(Boolean)
  }
})

function setOperation(op) {
  localParams.operation = op
}

// Load collections from API (using composable)
async function loadCollections() {
  await fetchCollections()
}

// Create new collection (using composable)
async function createCollection() {
  if (!newCollectionName.value.trim()) return

  creatingCollection.value = true
  try {
    const result = await createCollectionApi(newCollectionName.value.trim())
    if (result) {
      localParams.collection = newCollectionName.value.trim()
      showCreateModal.value = false
      newCollectionName.value = ''
    }
  } finally {
    creatingCollection.value = false
  }
}

// Sync changes to parent
watch(
  localParams,
  (newParams) => {
    emit('update:params', { ...newParams })
  },
  { deep: true }
)

// Sync from parent
watch(
  () => props.params,
  (newParams) => {
    Object.keys(newParams).forEach(key => {
      if (newParams[key] !== undefined && localParams[key] !== newParams[key]) {
        localParams[key] = newParams[key]
      }
    })
  },
  { deep: true }
)

// Load collections on mount
onMounted(() => {
  loadCollections()
})
</script>

<style scoped>
.vector-store-params {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Operation Tabs */
.operation-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 10px;
}

.operation-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.operation-tab:hover {
  color: #94a3b8;
  background: rgba(71, 85, 105, 0.2);
}

.operation-tab.active {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

/* Param Group */
.param-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.param-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
}

.param-value {
  margin-left: auto;
  color: #34d399;
  font-family: 'SF Mono', Monaco, monospace;
}

/* Refresh button */
.refresh-btn {
  margin-left: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-btn:hover:not(:disabled) {
  color: #94a3b8;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-btn .spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Create collection button */
.create-collection-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: transparent;
  border: 1px dashed rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #64748b;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.create-collection-btn:hover {
  border-color: rgba(16, 185, 129, 0.5);
  color: #34d399;
  background: rgba(16, 185, 129, 0.1);
}

/* Input */
.param-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  transition: all 0.2s ease;
}

.param-input:focus {
  outline: none;
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1);
}

/* Textarea */
.param-textarea {
  width: 100%;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  font-family: 'SF Mono', Monaco, monospace;
  resize: vertical;
  transition: all 0.2s ease;
}

.param-textarea:focus {
  outline: none;
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1);
}

/* Slider */
.param-slider {
  width: 100%;
  height: 6px;
  background: rgba(71, 85, 105, 0.4);
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
}

.param-slider::-webkit-slider-thumb {
  width: 16px;
  height: 16px;
  background: #34d399;
  border: none;
  border-radius: 50%;
  appearance: none;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.param-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.param-hint {
  margin: 0;
  font-size: 11px;
  color: #475569;
}

/* Advanced Section */
.advanced-section {
  border-top: 1px solid rgba(71, 85, 105, 0.3);
  padding-top: 12px;
}

.advanced-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 0;
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s ease;
}

.advanced-toggle:hover {
  color: #94a3b8;
}

.advanced-toggle svg {
  transition: transform 0.2s ease;
}

.advanced-toggle svg.rotated {
  transform: rotate(90deg);
}

.advanced-content {
  padding-top: 12px;
}

/* Collapse Transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 300px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.modal-content {
  width: 400px;
  max-width: 90vw;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #334155;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #334155;
}

.btn-secondary {
  padding: 8px 16px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: rgba(71, 85, 105, 0.4);
}

.btn-primary {
  padding: 8px 16px;
  background: rgba(16, 185, 129, 0.2);
  border: 1px solid rgba(16, 185, 129, 0.4);
  border-radius: 6px;
  color: #34d399;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: rgba(16, 185, 129, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
