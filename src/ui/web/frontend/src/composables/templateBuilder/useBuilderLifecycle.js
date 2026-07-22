import { ref, computed, watch, onMounted, onUnmounted, provide } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { DEFAULTS } from '@/config/defaults'
import { useCapabilitiesStore } from '../../stores/capabilitiesStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'
import { useModulesStore } from '../../stores/modulesStore'

/** Local-only lifecycle for the CE workflow builder. */
export function useBuilderLifecycle({
  elements,
  templateName,
  templateId,
  existingTemplateId,
  hasUnsavedChanges,
  isLoadingTemplate,
  autoSaveEnabled,
  activeTab,
  showSettingsPanel,
  showBrowserPanel: showBrowserPanelRef,
  executionStatus,
  executionNodeTimings,
  executionNodeStates,
  controlStore,
  hasBrowser,
  toggleDebugMode,
  autoSave,
  showToast,
  triggerImport,
  handleExport,
  loadExistingTemplate,
  activeDebugPanel,
  builderStore,
  builderCanvasRef,
  selectedWorkflowNode,
  onWorkflowNodeClick,
  createNodeFromModule,
  subflowBreadcrumbs,
  navigateToBreadcrumb,
  openSubflow,
  initSubflowElements,
  availableWorkflows,
}) {
  const route = useRoute()
  const { t, locale } = useI18n()
  const capabilitiesStore = useCapabilitiesStore()
  const modulesStore = useModulesStore()
  const testResult = ref(null)
  const isPageReady = ref(false)

  provide('availableWorkflows', availableWorkflows)

  const showResumePanel = computed(() => (
    executionStatus.value === 'failed' && controlStore.hasResumeOptions
  ))

  const timelineNodes = computed(() => {
    const timings = executionNodeTimings.value
    const states = executionNodeStates.value
    if (!timings || Object.keys(timings).length === 0) return []
    return Object.entries(timings).map(([nodeId, timing]) => {
      const node = elements.value.find(element => element.id === nodeId)
      return {
        id: nodeId,
        label: resolveModuleLabel(node?.data?.module, modulesStore) || nodeId.slice(0, 8),
        status: states[nodeId] || 'completed',
        startedAt: timing.startedAt,
        durationMs: timing.durationMs,
      }
    })
  })

  watch(elements, () => {
    if (!isLoadingTemplate.value) hasUnsavedChanges.value = true
  })
  watch(templateName, () => {
    if (!isLoadingTemplate.value) hasUnsavedChanges.value = true
  })
  watch(templateId, () => {
    if (!isLoadingTemplate.value) hasUnsavedChanges.value = true
  })

  let autoSaveTimer = null
  function clearAutoSaveTimer() {
    if (autoSaveTimer) clearTimeout(autoSaveTimer)
    autoSaveTimer = null
  }
  watch(existingTemplateId, clearAutoSaveTimer)
  watch(hasUnsavedChanges, (hasChanges, _previous, onCleanup) => {
    clearAutoSaveTimer()
    if (hasChanges && autoSaveEnabled.value && existingTemplateId.value && !isLoadingTemplate.value) {
      autoSaveTimer = setTimeout(() => autoSave(), DEFAULTS.TIMING.AUTO_SAVE_DELAY)
    }
    onCleanup(clearAutoSaveTimer)
  })
  watch(hasBrowser, value => {
    showBrowserPanelRef.value = Boolean(value)
  })

  function handleToggleAutoSave() { builderStore.toggleAutoSave() }
  function handleToggleSettings() { showSettingsPanel.value = !showSettingsPanel.value }
  function handleTidyNodes() { builderCanvasRef.value?.autoLayout?.() }
  function handleSettingsImport() { showSettingsPanel.value = false; triggerImport() }
  function handleSettingsExport() { showSettingsPanel.value = false; handleExport() }
  function handleTimelineNodeSelect(nodeId) {
    const node = elements.value.find(element => element.id === nodeId)
    if (node) onWorkflowNodeClick(node)
  }
  function handleToggleDebug() {
    const enabled = toggleDebugMode()
    if (enabled) activeTab.value = 'workflow'
  }
  function handleAddFirstNode() { builderStore.setShowModuleSelector(true, true) }
  function handleModuleSelect(module) {
    const newNode = createNodeFromModule(module)
    hasUnsavedChanges.value = true
    builderStore.setShowModuleSelector(false)
    selectedWorkflowNode.value = newNode
  }
  function closeModuleSelector() { builderStore.setShowModuleSelector(false) }
  function handleWorkflowNodeDelete({ deletedNodes }) {
    if (selectedWorkflowNode.value && deletedNodes.includes(selectedWorkflowNode.value.id)) {
      selectedWorkflowNode.value = null
    }
    hasUnsavedChanges.value = true
  }
  function handleContainerEdit({ nodeId, containerId }) {
    const containerNode = elements.value.find(element => element.id === nodeId)
    if (!containerNode) return
    const subflow = containerNode.data?.params?.subflow || { nodes: [], edges: [] }
    const flowId = containerId || nodeId
    initSubflowElements(flowId, subflow.nodes, subflow.edges)
    openSubflow({
      flowId,
      label: resolveModuleLabel(containerNode.data?.module, modulesStore) || 'Container',
      parentNodeId: nodeId,
      flowData: subflow,
    })
    activeTab.value = 'workflow'
  }
  function handleNavigateUp() {
    if (subflowBreadcrumbs.value.length >= 2) {
      navigateToBreadcrumb(subflowBreadcrumbs.value.at(-2).id)
    }
  }
  function handleNavigateRoot() {
    if (subflowBreadcrumbs.value.length) navigateToBreadcrumb(subflowBreadcrumbs.value[0].id)
  }
  async function loadAvailableModules(excludeTemplateId = null) {
    const result = await modulesStore.loadModules(locale.value, { excludeTemplateId })
    if (!result.ok) showToast(t('templateBuilder.messages.loadModulesFailed'), 'error')
  }
  async function reloadAvailableModules() {
    modulesStore.clearCache()
    await modulesStore.loadModules(locale.value, {
      forceRefresh: true,
      excludeTemplateId: existingTemplateId.value,
    })
  }

  onMounted(async () => {
    const routeTemplateId = route.params.id
    const existing = routeTemplateId && routeTemplateId !== 'new'
    await Promise.all([
      loadAvailableModules(existing ? routeTemplateId : null),
      existing ? loadExistingTemplate(routeTemplateId) : Promise.resolve(),
    ])
    isPageReady.value = true
  })
  onUnmounted(clearAutoSaveTimer)

  return {
    isPageReady,
    testResult,
    showResumePanel,
    timelineNodes,
    handleToggleAutoSave,
    handleToggleSettings,
    handleTidyNodes,
    handleSettingsImport,
    handleSettingsExport,
    handleTimelineNodeSelect,
    handleToggleDebug,
    handleAddFirstNode,
    handleModuleSelect,
    closeModuleSelector,
    handleWorkflowNodeDelete,
    handleContainerEdit,
    handleNavigateUp,
    handleNavigateRoot,
    reloadAvailableModules,
    capabilitiesStore,
    activeDebugPanel,
  }
}
