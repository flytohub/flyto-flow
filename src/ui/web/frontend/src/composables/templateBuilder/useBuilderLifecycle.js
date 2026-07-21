import { ref, computed, watch, onMounted, onUnmounted, provide, toRaw } from 'vue'
import { get } from '@/api/client'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { DEFAULTS } from '@/config/defaults'
import { useUserStore } from '../../stores/userStore'
import { useBuilderStore } from '../../stores/builderStore'
import { useCapabilitiesStore } from '../../stores/capabilitiesStore'
import { useCollaborationStore } from '../../stores/collaborationStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'
import { useModulesStore } from '../../stores/modulesStore'
import { authAPI } from '../../api/auth'
import { trackBuilder } from '../../utils/telemetryTracker'

/**
 * Consolidates collaboration watchers, lifecycle hooks, auto-save logic,
 * and miscellaneous UI handlers for the TemplateBuilder view.
 */
export function useBuilderLifecycle({
  // Core state
  elements,
  displayElements,
  templateName,
  templateId,
  templateDescription,
  existingTemplateId,
  templateCreatorId,
  templateMutability,
  templateVisibility,
  templateListed,
  isWorkflowVisible,
  hasUnsavedChanges,
  isLoadingTemplate,
  loadError,
  autoSaveEnabled,
  activeTab,
  showSettingsPanel,
  showBrowserPanel: showBrowserPanelRef,
  // Execution
  executionStatus,
  executionNodeTimings,
  executionNodeStates,
  controlStore,
  hasBrowser,
  screenshotMode,
  debugMode,
  currentExecutionId,
  isExecuting,
  startExecutionPolling,
  toggleDebugMode,
  // Composable functions
  autoSave,
  showToast,
  triggerImport,
  handleExport,
  loadExistingTemplate,
  trackSessionStart,
  trackSessionEnd,
  // Debug panels
  activeDebugPanel,
  handleReplayStarted,
  // Builder store & refs
  builderStore,
  builderCanvasRef,
  // Subflow
  selectedWorkflowNode,
  onWorkflowNodeClick,
  createNodeFromModule,
  subflowBreadcrumbs,
  navigateToBreadcrumb,
  openSubflow,
  initSubflowElements,
  // Modules
  modulesMetadata,
  // Error handling (defined in parent to avoid circular deps)
  errorHandling,
  availableWorkflows,
}) {
  const route = useRoute()
  const router = useRouter()
  const { t, locale } = useI18n()
  const userStore = useUserStore()
  const capabilitiesStore = useCapabilitiesStore()
  const collaborationStore = useCollaborationStore()
  const modulesStore = useModulesStore()

  // ===== Local UI State =====
  const showCollaborationPanel = ref(false)
  const showInviteModal = ref(false)
  const showUpgradeModal = ref(false)
  const testResult = ref(null)
  const isCloudExecution = import.meta.env.VITE_CLOUD_EXECUTION === 'true'

  // Provide availableWorkflows for ErrorTriggerParams component
  provide('availableWorkflows', availableWorkflows)

  // ===== Computed Properties =====
  const isWorkflowLocked = computed(() => {
    if (!existingTemplateId.value) return false
    if (collaborationStore.isConnected) return false
    return !isWorkflowVisible.value
  })

  const showResumePanel = computed(() => {
    return executionStatus.value === 'failed' && controlStore.hasResumeOptions
  })

  const isReadOnly = computed(() => {
    if (!existingTemplateId.value) return false
    const currentUser = authAPI.getLocalUser()
    const isOwner = currentUser?.uid === templateCreatorId.value
    if (isOwner) return false
    if (collaborationStore.isConnected) return false
    return templateMutability.value === 'locked'
  })

  const timelineNodes = computed(() => {
    const timings = executionNodeTimings.value
    const states = executionNodeStates.value
    if (!timings || Object.keys(timings).length === 0) return []

    return Object.entries(timings).map(([nodeId, timing]) => {
      const node = elements.value.find(el => el.id === nodeId)
      const label = resolveModuleLabel(node?.data?.module, modulesStore) || nodeId.slice(0, 8)

      return {
        id: nodeId,
        label,
        status: states[nodeId] || 'completed',
        startedAt: timing.startedAt,
        durationMs: timing.durationMs
      }
    })
  })

  // ===== Collaboration: Real-time Workflow Sync =====
  let _skipNextBroadcast = false

  watch(elements, () => {
    if (_skipNextBroadcast) {
      _skipNextBroadcast = false
      return
    }
    if (!isLoadingTemplate.value) {
      hasUnsavedChanges.value = true
    }
    if (collaborationStore.isConnected) {
      collaborationStore.broadcastWorkflowUpdate(toRaw(elements.value))
    }
  })

  watch(() => collaborationStore.incomingWorkflowUpdate, (update) => {
    if (!update?.elements) return
    _skipNextBroadcast = true
    displayElements.value = update.elements
  })

  watch(() => collaborationStore.sessionTerminated, (terminated) => {
    if (terminated && !collaborationStore.isOwner) {
      showToast(
        collaborationStore.error || t('collaboration.terminated', 'Collaboration session ended'),
        'info'
      )
      collaborationStore.leaveSession()
      router.push('/my-templates')
    }
  })

  // ===== Watchers =====
  watch(templateName, () => {
    if (!isLoadingTemplate.value) {
      hasUnsavedChanges.value = true
    }
  })

  watch(templateId, () => {
    if (!isLoadingTemplate.value) {
      hasUnsavedChanges.value = true
    }
  })

  // ===== Auto-Save Logic =====
  let autoSaveTimer = null

  function clearAutoSaveTimer() {
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer)
      autoSaveTimer = null
    }
  }

  watch(existingTemplateId, () => {
    clearAutoSaveTimer()
  })

  watch(hasUnsavedChanges, (hasChanges, _, onCleanup) => {
    clearAutoSaveTimer()

    if (hasChanges && autoSaveEnabled.value && existingTemplateId.value && !isLoadingTemplate.value) {
      autoSaveTimer = setTimeout(async () => {
        const result = await autoSave()
        if (!result.ok && result.reason !== 'already_saving') {
        }
      }, DEFAULTS.TIMING.AUTO_SAVE_DELAY)
    }

    onCleanup(clearAutoSaveTimer)
  })

  watch(hasBrowser, (has) => {
    showBrowserPanelRef.value = !!has
  })

  // ===== Handler Functions =====
  function handleToggleAutoSave() {
    builderStore.toggleAutoSave()
  }

  function handleToggleSettings() {
    showSettingsPanel.value = !showSettingsPanel.value
  }

  function handleTidyNodes() {
    builderCanvasRef.value?.autoLayout?.()
  }

  function handleSettingsImport() {
    showSettingsPanel.value = false
    triggerImport()
  }

  function handleSettingsExport() {
    showSettingsPanel.value = false
    handleExport()
  }

  async function handleTerminateCollaboration() {
    await collaborationStore.terminateSession()
    showCollaborationPanel.value = false
    showToast(t('collaboration.terminated', 'Collaboration session ended'), 'info')
  }

  function handleTimelineNodeSelect(nodeId) {
    const node = elements.value.find(el => el.id === nodeId)
    if (node) {
      onWorkflowNodeClick(node)
    }
  }

  function handleToggleDebug() {
    const isNowDebug = toggleDebugMode()
    trackBuilder.debugToggle(isNowDebug)
    if (isNowDebug && !isWorkflowLocked.value) {
      activeTab.value = 'workflow'
    }
  }

  // ===== Workflow Node Management =====
  function handleAddFirstNode() {
    builderStore.setShowModuleSelector(true, true)
  }

  function handleModuleSelect(module) {
    const newNode = createNodeFromModule(module)
    const moduleId = module.module || module.moduleId
    trackBuilder.nodeAdd(moduleId, existingTemplateId.value)
    hasUnsavedChanges.value = true
    builderStore.setShowModuleSelector(false)
    selectedWorkflowNode.value = newNode
  }

  function closeModuleSelector() {
    builderStore.setShowModuleSelector(false)
  }

  function handleWorkflowNodeDelete(event) {
    const { deletedNodes, deletedNodeTypes } = event

    if (deletedNodeTypes && deletedNodeTypes.length > 0) {
      deletedNodeTypes.forEach(nodeType => {
        trackBuilder.nodeDelete(nodeType, existingTemplateId.value)
      })
    }

    if (selectedWorkflowNode.value && deletedNodes.includes(selectedWorkflowNode.value.id)) {
      selectedWorkflowNode.value = null
    }
    hasUnsavedChanges.value = true
  }

  // ===== Container/Sandbox Edit Handler =====
  function handleContainerEdit(event) {
    const { nodeId, containerId } = event
    const containerNode = displayElements.value.find(el => el.id === nodeId)
    if (!containerNode) return

    const subflowData = containerNode.data?.params?.subflow || { nodes: [], edges: [] }
    const flowId = containerId || nodeId

    initSubflowElements(flowId, subflowData.nodes, subflowData.edges)

    openSubflow({
      flowId,
      label: resolveModuleLabel(containerNode.data?.module, modulesStore) || 'Container',
      parentNodeId: nodeId,
      flowData: subflowData
    })

    if (!isWorkflowLocked.value) {
      activeTab.value = 'workflow'
    }
  }

  // ===== Subflow Navigation Handlers =====
  function handleNavigateUp() {
    if (subflowBreadcrumbs.value.length >= 2) {
      const parentId = subflowBreadcrumbs.value[subflowBreadcrumbs.value.length - 2].id
      navigateToBreadcrumb(parentId)
    }
  }

  function handleNavigateRoot() {
    if (subflowBreadcrumbs.value.length > 0) {
      const rootId = subflowBreadcrumbs.value[0].id
      navigateToBreadcrumb(rootId)
    }
  }

  // ===== Module Loading =====
  async function loadAvailableModules(excludeTemplateId = null) {
    const result = await modulesStore.loadModules(locale.value, { excludeTemplateId })
    if (!result.ok) {
      showToast(t('templateBuilder.messages.loadModulesFailed'), 'error')
    }
  }

  async function reloadAvailableModules() {
    modulesStore.clearCache()
    await modulesStore.loadModules(locale.value, {
      forceRefresh: true,
      excludeTemplateId: existingTemplateId.value
    })
  }

  // ===== Lifecycle =====
  async function setupCollaboration(templateIdParam) {
    const currentUserId = userStore.user.uid
    const isOwner = templateCreatorId.value === currentUserId
    const inviteCode = route.query.invite

    if (inviteCode) {
      try {
        const { post: postReq } = await import('@/api/client')
        await postReq('/collaboration/join', { code: inviteCode })
      } catch (e) {
        // Ignore - will fail at WebSocket auth if not authorized
      }
    }

    const collabUser = {
      id: currentUserId,
      name: userStore.user.displayName,
      email: userStore.user.email,
      avatarUrl: userStore.user.avatarUrl,
      is_pro: capabilitiesStore.isPro,
    }

    if (isOwner || inviteCode) {
      collaborationStore.joinSession(templateIdParam, collabUser, { isOwner })
    } else {
      try {
        const data = await get(`/collaboration/${templateIdParam}/members`)
        if (data && !data.error) {
          if (data.members?.includes(currentUserId)) {
            collaborationStore.joinSession(templateIdParam, collabUser)
          }
        }
      } catch (e) {
        // Not a member - user needs to use invite code
      }
    }
  }

  const isPageReady = ref(false)

  onMounted(async () => {
    const templateIdParam = route.params.id
    const isExistingTemplate = templateIdParam && templateIdParam !== 'new'
    trackSessionStart(isExistingTemplate ? templateIdParam : null)

    const modulesPromise = loadAvailableModules(isExistingTemplate ? templateIdParam : null)
    const templatePromise = isExistingTemplate
      ? loadExistingTemplate(templateIdParam)
      : Promise.resolve()

    await Promise.all([modulesPromise, templatePromise])
    isPageReady.value = true

    if (isExistingTemplate && userStore.user) {
      setupCollaboration(templateIdParam)
    }
  })

  onUnmounted(() => {
    trackSessionEnd()
    clearAutoSaveTimer()
    collaborationStore.leaveSession()
  })

  return {
    // State
    isPageReady,
    showCollaborationPanel,
    showInviteModal,
    showUpgradeModal,
    testResult,
    isCloudExecution,
    // Computed
    showResumePanel,
    isReadOnly,
    timelineNodes,
    // Handlers
    handleToggleAutoSave,
    handleToggleSettings,
    handleTidyNodes,
    handleSettingsImport,
    handleSettingsExport,
    handleTerminateCollaboration,
    handleTimelineNodeSelect,
    handleToggleDebug,
    handleAddFirstNode,
    handleModuleSelect,
    closeModuleSelector,
    handleWorkflowNodeDelete,
    handleContainerEdit,
    handleNavigateUp,
    handleNavigateRoot,
    // Module loading
    reloadAvailableModules,
    // Stores exposed for template
    userStore,
    capabilitiesStore,
    collaborationStore,
  }
}
