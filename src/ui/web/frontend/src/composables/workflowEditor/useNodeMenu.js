/**
 * Node Menu Composable
 *
 * Handles menu state management for adding, inserting, and replacing nodes.
 * Dispatches module selection to the appropriate CRUD operation.
 */

import { generateNodeId } from './useCanvasOperations'

import { createMenuState } from './menuState'
import { createModuleFiltering } from './moduleFiltering'

/**
 * @param {Object} options
 * @param {Ref<Array>} options.nodes - Nodes array
 * @param {Ref<Array>} options.edges - Edges array
 * @param {Object} options.crud - Node CRUD operations from useNodeCrud
 * @param {Function} options.onSync - Callback to sync to parent
 * @param {Function} options.onBeforeAdd - Callback before adding a node (for undo/redo history)
 */
export function useNodeMenu({ nodes, edges, crud, onSync, onBeforeAdd }) {
  const menu = createMenuState(nodes)
  const filtering = createModuleFiltering()

  /**
   * Open add node menu
   */
  async function openAddNodeMenu({
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
    menu.setPendingConnection({
      nodeId,
      sourceHandle,
      targetHandle,
      caseColor,
      caseId,
      filter,
      subNodeType,
      position,
      pendingCase
    })

    // Standalone node creation (no source node)
    if (!nodeId && position) {
      filtering.clearCompatibleModules()
      menu.openMenu()
      return
    }

    // AI Agent sub-nodes — skip compatible API
    if (targetHandle) {
      filtering.clearCompatibleModules()
      menu.openMenu()
      return
    }

    // Specific source handle — skip compatible filter
    if (sourceHandle) {
      filtering.clearCompatibleModules()
      menu.openMenu()
      return
    }

    // Fetch connectable modules from API (Type Safety)
    const sourceNode = nodes.value.find(n => n.id === nodeId)
    const sourceModuleId = sourceNode?.data?.module

    if (sourceModuleId) {
      await filtering.fetchCompatibleModules(sourceModuleId)
    } else {
      filtering.clearCompatibleModules()
    }

    menu.openMenu()
  }

  /**
   * Open menu for inserting a node on an edge
   */
  async function openInsertNodeMenu(edge) {
    if (!edge) return

    const sourceNode = nodes.value.find(n => n.id === edge.source)
    const targetNode = nodes.value.find(n => n.id === edge.target)

    if (!sourceNode || !targetNode) {
      return
    }

    menu.setPendingInsertEdge(edge)

    const sourceModuleId = sourceNode.data?.module
    const targetModuleId = targetNode.data?.module
    if (sourceModuleId || targetModuleId) {
      await filtering.fetchReplacementCompatibleModules(sourceModuleId, targetModuleId)
    } else {
      filtering.clearCompatibleModules()
    }

    menu.openMenu()
  }

  /**
   * Open menu for replacing a node with another module
   */
  async function openReplaceNodeMenu(nodeId, currentModuleId) {
    if (!nodeId) return

    menu.setPendingReplaceNode(nodeId)

    const { upstreamModuleId, downstreamModuleId } = crud.getNodeConnections(nodeId)
    await filtering.fetchReplacementCompatibleModules(upstreamModuleId, downstreamModuleId)

    menu.openMenu()
  }

  /**
   * Handle module selection from menu
   */
  async function handleModuleSelected(module) {
    onBeforeAdd?.()

    const newId = generateNodeId()
    const moduleId = module.moduleId || module.module
    const pendingState = menu.getPendingState()

    // Node replacement mode
    if (pendingState.replaceNodeId) {
      crud.replaceNode(pendingState.replaceNodeId, moduleId, module)
      closeMenu()
      onSync?.()
      return
    }

    // Edge insertion mode
    if (pendingState.insertEdge) {
      const result = await crud.insertNodeOnEdge(newId, moduleId, module, pendingState.insertEdge)
      closeMenu()
      if (result) {
        onSync?.()
      }
      return
    }

    // Template selection
    if (moduleId?.startsWith('template.invoke:') || module.templateId) {
      crud.createTemplateNode(newId, module, pendingState)
      closeMenu()
      onSync?.()
      return
    }

    // Standalone node creation (no parent node)
    if (!pendingState.sourceNodeId) {
      crud.createStandaloneNode(newId, moduleId, module, pendingState.position)
      closeMenu()
      onSync?.()
      return
    }

    const parentNode = nodes.value.find(n => n.id === pendingState.sourceNodeId)
    if (!parentNode) return

    // AI Agent sub-node case (reverse connection)
    if (pendingState.targetHandle) {
      crud.createSubNode(parentNode, newId, moduleId, module, pendingState)
      closeMenu()
      onSync?.()
      return
    }

    // Normal case (forward connection)
    crud.createForwardNode(parentNode, newId, moduleId, module, pendingState)
    closeMenu()
    onSync?.()
  }

  /**
   * Close menu and reset state
   */
  function closeMenu() {
    menu.closeMenu()
    filtering.clearCompatibleModules()
  }

  return {
    // Menu state
    menuOpen: menu.menuOpen,
    pendingSourceNode: menu.pendingSourceNode,
    pendingModuleFilter: menu.pendingModuleFilter,
    isInsertionMode: menu.isInsertionMode,
    pendingInsertEdge: menu.pendingInsertEdge,
    isReplaceMode: menu.isReplaceMode,
    pendingReplaceNodeId: menu.pendingReplaceNodeId,

    // Filtering state
    isLoadingCompatible: filtering.isLoadingCompatible,
    filterModules: filtering.filterModules,

    // Menu methods
    openAddNodeMenu,
    openInsertNodeMenu,
    openReplaceNodeMenu,
    handleModuleSelected,
    closeMenu
  }
}
