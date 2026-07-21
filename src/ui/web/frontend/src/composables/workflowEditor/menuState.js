/**
 * Menu State — Add/Insert/Replace node menu state management
 *
 * Manages the reactive state for the module selection menu,
 * including pending connection info, insertion mode, and replacement mode.
 */

import { ref, computed } from 'vue'

/**
 * Creates the menu state subsystem.
 *
 * @param {Ref<Array>} nodes - Reactive nodes array (used for pendingSourceNode lookup)
 * @returns {Object} Menu state and methods
 */
export function createMenuState(nodes) {
  const menuOpen = ref(false)

  // Pending connection state
  const pendingSourceNodeId = ref(null)
  const pendingSourceHandle = ref(null)
  const pendingTargetHandle = ref(null)
  const pendingSubNodeType = ref(null)
  const pendingCaseColor = ref(null)
  const pendingCaseId = ref(null)
  const pendingCaseObj = ref(null)
  const pendingModuleFilter = ref(null)
  const pendingPosition = ref(null)

  // Edge insertion state
  const pendingInsertEdge = ref(null)

  // Node replacement state
  const pendingReplaceNodeId = ref(null)

  // Computed states
  const isInsertionMode = computed(() => !!pendingInsertEdge.value)
  const isReplaceMode = computed(() => !!pendingReplaceNodeId.value)
  const pendingSourceNode = computed(() => {
    if (!pendingSourceNodeId.value) return null
    return nodes.value.find(n => n.id === pendingSourceNodeId.value)
  })

  function setPendingConnection({
    nodeId = null,
    sourceHandle = null,
    targetHandle = null,
    caseColor = null,
    caseId = null,
    filter = null,
    subNodeType = null,
    position = null,
    pendingCase = null
  }) {
    pendingSourceNodeId.value = nodeId
    pendingSourceHandle.value = sourceHandle
    pendingTargetHandle.value = targetHandle
    pendingSubNodeType.value = subNodeType
    pendingCaseColor.value = caseColor
    pendingCaseId.value = caseId
    pendingCaseObj.value = pendingCase
    pendingModuleFilter.value = filter
    pendingPosition.value = position
  }

  function setPendingInsertEdge(edge) {
    pendingInsertEdge.value = edge
    pendingSourceNodeId.value = null
    pendingSourceHandle.value = null
    pendingTargetHandle.value = null
    pendingSubNodeType.value = null
    pendingCaseColor.value = null
    pendingCaseId.value = null
    pendingCaseObj.value = null
    pendingModuleFilter.value = null
    pendingPosition.value = null
  }

  function setPendingReplaceNode(nodeId) {
    pendingReplaceNodeId.value = nodeId
  }

  function openMenu() {
    menuOpen.value = true
  }

  function closeMenu() {
    menuOpen.value = false
    pendingSourceNodeId.value = null
    pendingSourceHandle.value = null
    pendingTargetHandle.value = null
    pendingSubNodeType.value = null
    pendingCaseColor.value = null
    pendingCaseId.value = null
    pendingCaseObj.value = null
    pendingModuleFilter.value = null
    pendingPosition.value = null
    pendingInsertEdge.value = null
    pendingReplaceNodeId.value = null
  }

  function getPendingState() {
    return {
      sourceNodeId: pendingSourceNodeId.value,
      sourceHandle: pendingSourceHandle.value,
      targetHandle: pendingTargetHandle.value,
      subNodeType: pendingSubNodeType.value,
      caseColor: pendingCaseColor.value,
      caseId: pendingCaseId.value,
      pendingCase: pendingCaseObj.value,
      filter: pendingModuleFilter.value,
      position: pendingPosition.value,
      insertEdge: pendingInsertEdge.value,
      replaceNodeId: pendingReplaceNodeId.value
    }
  }

  return {
    menuOpen,
    pendingSourceNode,
    pendingModuleFilter,
    isInsertionMode,
    pendingInsertEdge,
    isReplaceMode,
    pendingReplaceNodeId,
    setPendingConnection,
    setPendingInsertEdge,
    setPendingReplaceNode,
    openMenu,
    closeMenu,
    getPendingState
  }
}
