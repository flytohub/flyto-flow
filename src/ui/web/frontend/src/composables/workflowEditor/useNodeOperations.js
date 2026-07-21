/**
 * Node Operations Composable (Facade)
 *
 * Composes sub-composables for all node operations on the workflow canvas:
 * - useNodeCrud      — creation, insertion, replacement
 * - useNodeDeletion  — deletion with reconnect/cascade dialogs
 * - useNodeMenu      — menu state, module filtering, selection dispatch
 *
 * This facade preserves the original public API so that consumers
 * (e.g. WorkflowCanvas.vue) require no changes.
 */

import { useNodeCrud } from './useNodeCrud'
import { useNodeDeletion } from './useNodeDeletion'
import { useNodeMenu } from './useNodeMenu'

/**
 * @param {Object} options
 * @param {Ref<Array>} options.nodes - Nodes array
 * @param {Ref<Array>} options.edges - Edges array
 * @param {Array} options.caseColors - Switch case colors
 * @param {Function} options.onSync - Callback to sync to parent
 * @param {Function} options.onBeforeAdd - Callback before adding a node (for undo/redo history)
 * @param {Function} options.onDelete - Callback when nodes deleted
 */
export function useNodeOperations({ nodes, edges, caseColors = [], onSync, onBeforeAdd, onDelete }) {
  const crud = useNodeCrud({ nodes, edges, caseColors })
  const deletion = useNodeDeletion({ nodes, edges, onSync, onDelete })
  const menu = useNodeMenu({ nodes, edges, crud, onSync, onBeforeAdd })

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
    isLoadingCompatible: menu.isLoadingCompatible,

    // Deletion dialog state
    showReconnectDialog: deletion.showReconnectDialog,
    pendingDeleteNodeId: deletion.pendingDeleteNodeId,
    pendingReconnectInfo: deletion.pendingReconnectInfo,
    reconnectDialogTitle: deletion.reconnectDialogTitle,
    reconnectDialogMessage: deletion.reconnectDialogMessage,
    showDeleteChildrenDialog: deletion.showDeleteChildrenDialog,
    pendingDeleteChildCount: deletion.pendingDeleteChildCount,
    pendingDeleteChildrenInfo: deletion.pendingDeleteChildrenInfo,

    // Addition methods
    filterModules: menu.filterModules,
    openAddNodeMenu: menu.openAddNodeMenu,
    openInsertNodeMenu: menu.openInsertNodeMenu,
    openReplaceNodeMenu: menu.openReplaceNodeMenu,
    handleModuleSelected: menu.handleModuleSelected,
    closeMenu: menu.closeMenu,

    // Deletion methods
    hasPathBetween: deletion.hasPathBetween,
    handleDeleteEdge: deletion.handleDeleteEdge,
    requestDeleteNode: deletion.requestDeleteNode,
    confirmReconnect: deletion.confirmReconnect,
    skipReconnect: deletion.skipReconnect,
    cancelDelete: deletion.cancelDelete,
    handleMergeToChild: deletion.handleMergeToChild,
    handleDeleteAllChildren: deletion.handleDeleteAllChildren,
    cancelDeleteWithChildren: deletion.cancelDeleteWithChildren
  }
}
