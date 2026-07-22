import { ref, computed, watch, nextTick } from 'vue'
import { generateNodeId, createNode } from './useCanvasOperations'
import { HISTORY_ACTIONS } from './useCanvasHistory'

export function useCanvasEvents({
  nodes,
  edges,
  props,
  emit,
  controlStore,
  toast,
  t,
  updateNodeInternals,
  saveHistoryState,
  syncToParent,
  requestDeleteNode,
  openAddNodeMenu,
  openInsertNodeMenu,
  openReplaceNodeMenu,
  handleDeleteEdge,
  handleDebugNodeClick,
  setCenter,
  menuOpen,
  showCaseSelector,
  cancelCaseSelection,
  showNodeSearch,
  copySelectedNodes,
  pasteNodes,
  handleFitView,
  autoLayout,
  historyUndo,
  historyRedo,
  canUndo,
  canRedo,
}) {
  const selectedEdgeId = ref(null)
  const actionBarNode = ref(null)
  const contextMenuVisible = ref(false)
  const contextMenuPosition = ref({ x: 0, y: 0 })
  const contextMenuNode = ref(null)
  const showSaveAsTemplate = ref(false)
  const saveAsTemplateNode = ref(null)

  watch(menuOpen, (isOpen) => {
    if (isOpen) actionBarNode.value = null
  })

  watch(nodes, (currentNodes) => {
    if (actionBarNode.value && !currentNodes.find(n => n.id === actionBarNode.value.id)) {
      actionBarNode.value = null
    }
  }, { deep: true })

  const hasActionBarNodeOutput = computed(() => {
    if (!actionBarNode.value) return false
    return controlStore.getNodeOutput(actionBarNode.value.id) !== null
  })

  function handleNodeClick(event) {
    if (props.debugMode) { handleDebugNodeClick(event.node.id); return }
    actionBarNode.value = event.node
    emit('node-click', event)
  }

  function handleNodeContextMenuEvent({ event, node }) {
    event.preventDefault()
    contextMenuNode.value = node
    contextMenuPosition.value = { x: event.clientX, y: event.clientY }
    contextMenuVisible.value = true
  }

  function closeContextMenu() {
    contextMenuVisible.value = false
  }

  function handleEdgeClick({ edge }) { selectedEdgeId.value = edge.id }

  function handleEdgeInsertNode(edgeData) {
    const edge = edges.value.find(e => e.id === edgeData.edgeId)
    if (!edge) return
    openInsertNodeMenu(edge)
  }

  function handleNodeDoubleClick({ node }) { emit('toggle-checkpoint', node.id) }

  function handleToggleCheckpoint(nodeId) { emit('toggle-checkpoint', nodeId) }
  function handleRetryNode({ nodeId }) { emit('retry-node', { nodeId }) }
  function handleEditContainer(payload) { emit('edit-container', payload) }

  function handleReplaceNodeRequest({ nodeId, moduleId }) {
    saveHistoryState(HISTORY_ACTIONS.NODE_UPDATE, { nodeId })
    openReplaceNodeMenu(nodeId, moduleId)
  }

  function handleActionBarDelete(nodeId) {
    saveHistoryState(HISTORY_ACTIONS.NODE_DELETE, { nodeId })
    requestDeleteNode(nodeId)
    actionBarNode.value = null
  }

  function handleTogglePin(nodeId) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (!node) return

    if (node.data.isPinned) {
      saveHistoryState(HISTORY_ACTIONS.NODE_UPDATE, { nodeId, field: 'isPinned' })
      node.data.isPinned = false
      node.data.pinnedOutput = null
      node.data.pinnedAt = null
      syncToParent()
    } else {
      const output = controlStore.getNodeOutput(nodeId)
      if (!output) {
        toast.warning(t('workflow.pinRequiresOutput', 'Run the node first to generate output before pinning'))
        return
      }
      saveHistoryState(HISTORY_ACTIONS.NODE_UPDATE, { nodeId, field: 'isPinned' })
      node.data.isPinned = true
      node.data.pinnedOutput = output
      node.data.pinnedAt = Date.now()
      syncToParent()
    }
  }

  function handleToggleDisabled(nodeId) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (!node) return
    saveHistoryState(HISTORY_ACTIONS.NODE_UPDATE, { nodeId, field: 'disabled' })
    if (!node.data) node.data = {}
    node.data.disabled = !node.data.disabled
    syncToParent()
  }

  function handleToggleCollapse(nodeId) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (!node) return

    saveHistoryState(HISTORY_ACTIONS.NODE_UPDATE, { nodeId, field: 'collapsed' })
    if (!node.data) node.data = {}
    const wasCollapsed = node.data.collapsed
    node.data.collapsed = !wasCollapsed

    const moduleId = node.data.module
    const dims = props.modulesMetadata?.[moduleId]?.uiConfig?.dimensions
    const nodeW = dims?.width ?? 240
    const nodeH = dims?.height ?? 76
    const dx = (nodeW - 64) / 2
    const dy = (nodeH - 64) / 2
    if (!wasCollapsed) { node.position.x += dx; node.position.y += dy }
    else { node.position.x -= dx; node.position.y -= dy }

    syncToParent()
    nextTick(() => { updateNodeInternals([nodeId]) })
  }

  function handleStickyNoteUpdate({ nodeId, updates }) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (!node) return
    saveHistoryState(HISTORY_ACTIONS.NODE_UPDATE, { nodeId, field: 'stickyNote' })
    if (!node.data) node.data = {}
    Object.assign(node.data, updates)
    syncToParent()
  }

  function handlePaneClick() {
    selectedEdgeId.value = null
    actionBarNode.value = null
  }

  function handleAddNodeRequest(params) { openAddNodeMenu(params) }

  function handleDeleteNodeRequest({ nodeId }) {
    saveHistoryState(HISTORY_ACTIONS.NODE_DELETE, { nodeId })
    requestDeleteNode(nodeId)
    if (actionBarNode.value?.id === nodeId) actionBarNode.value = null
  }

  function handleSearchSelect(node) {
    if (!node) return
    nodes.value = nodes.value.map(n => ({ ...n, selected: n.id === node.id }))
    setCenter(node.position.x + 100, node.position.y + 50, { zoom: 1, duration: 300 })
    actionBarNode.value = node
    emit('node-click', { node })
  }

  function handleSaveAsTemplate(node) {
    saveAsTemplateNode.value = node
    showSaveAsTemplate.value = true
  }

  function handleDuplicateNode(node) {
    if (!node) return
    const newId = generateNodeId()
    const newNode = createNode({
      id: newId,
      type: node.type || 'custom',
      position: { x: (node.position?.x || 0) + 40, y: (node.position?.y || 0) + 40 },
      data: { ...node.data, params: { ...node.data?.params } }
    })
    nodes.value = [...nodes.value, newNode]
    syncToParent()
  }

  // === History: Undo/Redo ===
  function handleUndo() {
    if (!canUndo.value) { toast.info(t('workflow.history.nothingToUndo')); return }
    const restoredState = historyUndo({ nodes: nodes.value, edges: edges.value })
    if (restoredState) { nodes.value = restoredState.nodes; edges.value = restoredState.edges; syncToParent(); toast.success(t('workflow.history.undone')) }
  }

  function handleRedo() {
    if (!canRedo.value) { toast.info(t('workflow.history.nothingToRedo')); return }
    const restoredState = historyRedo({ nodes: nodes.value, edges: edges.value })
    if (restoredState) { nodes.value = restoredState.nodes; edges.value = restoredState.edges; syncToParent(); toast.success(t('workflow.history.redone')) }
  }

  // === Clipboard ===
  async function handleCopy() {
    const success = await copySelectedNodes()
    if (success) toast.success(t('workflow.clipboard.copied', { count: nodes.value.filter(n => n.selected).length }))
    else toast.warning(t('workflow.clipboard.nothingToCopy'))
  }

  async function handlePaste() {
    const result = await pasteNodes()
    if (result && result.nodes.length > 0) toast.success(t('workflow.clipboard.pasted', { count: result.nodes.length }))
  }

  async function handleCut() {
    const selectedNodes = nodes.value.filter(n => n.selected)
    if (selectedNodes.length === 0) return
    const success = await copySelectedNodes()
    if (success) {
      saveHistoryState(HISTORY_ACTIONS.NODE_DELETE, { nodeIds: selectedNodes.map(n => n.id) })
      const nodeIds = new Set(selectedNodes.map(n => n.id))
      nodes.value = nodes.value.filter(n => !nodeIds.has(n.id))
      edges.value = edges.value.filter(e => !nodeIds.has(e.source) && !nodeIds.has(e.target))
      syncToParent()
      toast.success(t('workflow.clipboard.cut', { count: selectedNodes.length }))
    }
  }

  // === Sticky Note ===
  function createStickyNote() {
    saveHistoryState(HISTORY_ACTIONS.NODE_ADD, { type: 'sticky-note' })
    const newId = generateNodeId()
    let position
    if (nodes.value.length === 0) position = { x: 250, y: 150 }
    else {
      const maxX = Math.max(...nodes.value.map(n => n.position.x))
      const maxY = Math.max(...nodes.value.map(n => n.position.y))
      position = { x: maxX + 50, y: maxY + 100 }
    }
    const stickyNode = createNode({
      id: newId, type: 'sticky', position, label: '',
      data: { module: 'sticky-note', type: 'sticky', title: '', content: '', color: 'yellow', width: 200, height: 150 }
    })
    nodes.value = [...nodes.value, stickyNode]
    syncToParent()
    toast.success(t('workflowCanvas.stickyNoteCreated', 'Sticky note created'))
  }

  // === Auto Layout ===
  async function handleAutoLayout() {
    if (nodes.value.length === 0) return
    nodes.value = await autoLayout(nodes.value, edges.value)
    syncToParent()
    nextTick(() => { updateNodeInternals(nodes.value.map(n => n.id)) })
    setTimeout(() => handleFitView(), 50)
  }

  // === Keyboard Handler ===
  let arrowKeyHistorySaved = false
  let arrowKeyTimer = null

  function onKeyDown(event) {
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return

    if ((event.key === 'Delete' || event.key === 'Backspace') && selectedEdgeId.value) {
      event.preventDefault()
      saveHistoryState(HISTORY_ACTIONS.EDGE_DELETE, { edgeId: selectedEdgeId.value })
      handleDeleteEdge(selectedEdgeId.value)
      selectedEdgeId.value = null
      return
    }

    if (event.key === 'Tab') { event.preventDefault(); showNodeSearch.value = true; return }
    if (event.key === 'n' || event.key === 'N') { event.preventDefault(); openAddNodeMenu({}); return }
    if ((event.ctrlKey || event.metaKey) && event.key === 'a') { event.preventDefault(); nodes.value = nodes.value.map(node => ({ ...node, selected: true })); return }
    if ((event.ctrlKey || event.metaKey) && event.key === 'f') { event.preventDefault(); showNodeSearch.value = true; return }
    if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) { event.preventDefault(); handleUndo(); return }
    if ((event.ctrlKey || event.metaKey) && event.key === 'z' && event.shiftKey) { event.preventDefault(); handleRedo(); return }
    if ((event.ctrlKey || event.metaKey) && event.key === 'y') { event.preventDefault(); handleRedo(); return }
    if (event.shiftKey && (event.key === 's' || event.key === 'S') && !event.ctrlKey && !event.metaKey) { event.preventDefault(); createStickyNote(); return }
    if ((event.ctrlKey || event.metaKey) && event.key === 'c') { if (nodes.value.filter(n => n.selected).length > 0) { event.preventDefault(); handleCopy(); return } }
    if ((event.ctrlKey || event.metaKey) && event.key === 'v') { event.preventDefault(); handlePaste(); return }
    if ((event.ctrlKey || event.metaKey) && event.key === 'x') { if (nodes.value.filter(n => n.selected).length > 0) { event.preventDefault(); handleCut(); return } }
    if (event.key === 'Escape') { if (showCaseSelector.value) cancelCaseSelection(); return }

    const arrowKeyOffsets = { ArrowUp: { x: 0, y: -20 }, ArrowDown: { x: 0, y: 20 }, ArrowLeft: { x: -20, y: 0 }, ArrowRight: { x: 20, y: 0 } }
    if (arrowKeyOffsets[event.key]) {
      const selectedNodes = nodes.value.filter(node => node.selected)
      if (selectedNodes.length > 0) {
        event.preventDefault()
        if (!arrowKeyHistorySaved) {
          saveHistoryState(HISTORY_ACTIONS.NODE_MOVE, { nodeIds: selectedNodes.map(n => n.id) })
          arrowKeyHistorySaved = true
        }
        const offset = arrowKeyOffsets[event.key]
        nodes.value = nodes.value.map(node => {
          if (node.selected) return { ...node, position: { x: node.position.x + offset.x, y: node.position.y + offset.y } }
          return node
        })
        syncToParent()
        clearTimeout(arrowKeyTimer)
        arrowKeyTimer = setTimeout(() => { arrowKeyHistorySaved = false }, 500)
      }
    }
  }

  function cleanupArrowKeyTimer() {
    if (arrowKeyTimer) { clearTimeout(arrowKeyTimer); arrowKeyTimer = null }
  }

  return {
    selectedEdgeId,
    actionBarNode,
    hasActionBarNodeOutput,
    contextMenuVisible,
    contextMenuPosition,
    contextMenuNode,
    closeContextMenu,
    showSaveAsTemplate,
    saveAsTemplateNode,
    handleNodeClick,
    handleNodeContextMenuEvent,
    handleEdgeClick,
    handleEdgeInsertNode,
    handleNodeDoubleClick,
    handleToggleCheckpoint,
    handleRetryNode,
    handleEditContainer,
    handleReplaceNodeRequest,
    handleActionBarDelete,
    handleTogglePin,
    handleToggleDisabled,
    handleToggleCollapse,
    handleStickyNoteUpdate,
    handlePaneClick,
    handleAddNodeRequest,
    handleDeleteNodeRequest,
    handleSearchSelect,
    handleSaveAsTemplate,
    handleDuplicateNode,
    handleAutoLayout,
    handleEdgeClick,
    onKeyDown,
    cleanupArrowKeyTimer,
  }
}
