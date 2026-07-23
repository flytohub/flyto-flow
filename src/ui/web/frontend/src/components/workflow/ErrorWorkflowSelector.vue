<script setup>
/**
 * Error Workflow Selector Component
 * Allows users to select a workflow to trigger when errors occur.
 */
import { ref, computed, onMounted, watch } from 'vue'
import { get } from '@/api/client'
import { useI18n } from 'vue-i18n'
import { AlertTriangle, ChevronDown, Check, X, Workflow, Search } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: String, default: '' },
  currentWorkflowId: { type: String, default: '' },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const workflows = ref([])
const loading = ref(false)
const searchQuery = ref('')

const selectedWorkflow = computed(() => workflows.value.find(w => w.id === props.modelValue))

const filteredWorkflows = computed(() => {
  let list = workflows.value.filter(w => w.id !== props.currentWorkflowId)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(w => w.name.toLowerCase().includes(q))
  }
  return list
})

const fetchWorkflows = async () => {
  loading.value = true
  try {
    const data = await get('/templates/', { params: { page: 1, page_size: 500 } })
    if (data?.ok) workflows.value = data.items || []
  } catch (e) { console.error('[ErrorWorkflowSelector] fetch failed:', e) }
  finally { loading.value = false }
}

const selectWorkflow = (workflow) => {
  emit('update:modelValue', workflow.id)
  isOpen.value = false
  searchQuery.value = ''
}

const clearSelection = () => {
  emit('update:modelValue', '')
  isOpen.value = false
}

onMounted(() => fetchWorkflows())
watch(isOpen, (val) => { if (val) searchQuery.value = '' })
</script>

<template>
  <div class="error-workflow-selector" :class="{ disabled, open: isOpen }">
    <div class="selector-header">
      <AlertTriangle :size="14" class="header-icon" />
      <span class="header-title">{{ t('execution.errorWorkflow.title') }}</span>
    </div>
    <p class="selector-description">{{ t('execution.errorWorkflow.description') }}</p>

    <div class="selector-trigger" @click="!disabled && (isOpen = !isOpen)">
      <div class="selected-value">
        <Workflow v-if="selectedWorkflow" :size="14" class="workflow-icon" />
        <span :class="{ placeholder: !selectedWorkflow }">
          {{ selectedWorkflow ? selectedWorkflow.name : t('execution.errorWorkflow.select') }}
        </span>
      </div>
      <div class="trigger-actions">
        <button v-if="selectedWorkflow" class="clear-btn" @click.stop="clearSelection">
          <X :size="14" />
        </button>
        <ChevronDown :size="16" class="chevron" :class="{ rotated: isOpen }" />
      </div>
    </div>

    <Transition name="dropdown">
      <div v-if="isOpen" class="dropdown">
        <div class="search-box">
          <Search :size="14" />
          <AppInput v-model="searchQuery" :placeholder="t('common.search')" class="!pl-10" />
        </div>

        <div v-if="loading" class="dropdown-loading"><div class="spinner" /></div>
        <div v-else-if="!filteredWorkflows.length" class="dropdown-empty">
          <Workflow :size="20" /><span>{{ t('execution.errorWorkflow.none') }}</span>
        </div>
        <div v-else class="workflow-list">
          <div
            v-for="wf in filteredWorkflows"
            :key="wf.id"
            class="workflow-item"
            :class="{ selected: wf.id === modelValue }"
            @click="selectWorkflow(wf)"
          >
            <Workflow :size="14" class="item-icon" />
            <div class="item-info">
              <span class="item-name">{{ wf.name }}</span>
              <span v-if="wf.description" class="item-desc">{{ wf.description }}</span>
            </div>
            <Check v-if="wf.id === modelValue" :size="14" class="check-icon" />
          </div>
        </div>
      </div>
    </Transition>
    <div v-if="isOpen" class="backdrop" @click="isOpen = false" />
  </div>
</template>

<style scoped>
.error-workflow-selector { position: relative; padding: 16px; background: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.2); border-radius: 12px; }
.error-workflow-selector.disabled { opacity: 0.6; pointer-events: none; }
.selector-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.header-icon { color: #f87171; }
.header-title { font-size: 13px; font-weight: 600; color: #f1f5f9; }
.selector-description { font-size: 11px; color: #94a3b8; margin: 0 0 12px; }
.selector-trigger { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; background: rgba(30,41,59,0.6); border: 1px solid rgba(148,163,184,0.2); border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.selector-trigger:hover { border-color: rgba(239,68,68,0.4); }
.error-workflow-selector.open .selector-trigger { border-color: #ef4444; }
.selected-value { display: flex; align-items: center; gap: 8px; flex: 1; }
.workflow-icon { color: #f87171; }
.selected-value span { font-size: 13px; color: #f1f5f9; }
.selected-value span.placeholder { color: #64748b; }
.trigger-actions { display: flex; align-items: center; gap: 4px; }
.clear-btn { padding: 4px; background: rgba(239,68,68,0.1); border: none; border-radius: 4px; color: #f87171; cursor: pointer; }
.clear-btn:hover { background: rgba(239,68,68,0.2); }
.chevron { color: #64748b; transition: transform 0.2s; }
.chevron.rotated { transform: rotate(180deg); }
.dropdown { position: absolute; top: calc(100% + 4px); left: 0; right: 0; background: rgba(30,41,59,0.98); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); z-index: 100; max-height: 320px; overflow: hidden; display: flex; flex-direction: column; }
.search-box { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-bottom: 1px solid rgba(51,65,85,0.5); color: #64748b; }
.search-box input { flex: 1; background: none; border: none; color: #f1f5f9; font-size: 13px; outline: none; }
.search-box input::placeholder { color: #64748b; }
.dropdown-loading, .dropdown-empty { display: flex; flex-direction: column; align-items: center; padding: 24px; gap: 8px; color: #64748b; font-size: 12px; }
.spinner { width: 20px; height: 20px; border: 2px solid rgba(239,68,68,0.2); border-top-color: #ef4444; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.workflow-list { flex: 1; overflow-y: auto; padding: 4px; }
.workflow-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 6px; cursor: pointer; transition: background 0.15s; }
.workflow-item:hover { background: rgba(239,68,68,0.1); }
.workflow-item.selected { background: rgba(239,68,68,0.15); }
.item-icon { color: #f87171; flex-shrink: 0; }
.item-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.item-name { font-size: 13px; color: #f1f5f9; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-desc { font-size: 11px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.check-icon { color: #10b981; flex-shrink: 0; }
.backdrop { position: fixed; inset: 0; z-index: 99; }
.dropdown-enter-active, .dropdown-leave-active { transition: all 0.2s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
