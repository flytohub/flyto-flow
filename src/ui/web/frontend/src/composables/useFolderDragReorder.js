/**
 * Folder Drag Reorder composable — drag-and-drop folder reorder logic
 * Manages drag state for sidebar folder reordering and template-to-folder drops.
 */
import { ref } from 'vue'

export function useFolderDragReorder({ localFolderOrder, emit, clearSelection }) {
  const dragType = ref(null)
  const folderDropIdx = ref(-1)
  const draggingFolderIdx = ref(-1)
  const dragOverFolderId = ref(null)

  // ---- Folder Drag (sidebar reorder) ----
  function onFolderDragStart(e, folderId, idx) {
    dragType.value = 'folder'
    draggingFolderIdx.value = idx
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', folderId)
  }

  function onFolderDragEnd() {
    dragType.value = null
    folderDropIdx.value = -1
    draggingFolderIdx.value = -1
    dragOverFolderId.value = null
  }

  // ---- Sidebar drop zone (handles both template-to-folder and folder-reorder) ----
  function onDragOverSidebar(e, folderId, idx) {
    e.dataTransfer.dropEffect = 'move'
    if (dragType.value === 'folder') {
      // Determine drop position (above or below)
      const rect = e.currentTarget.getBoundingClientRect()
      const midY = rect.top + rect.height / 2
      folderDropIdx.value = e.clientY < midY ? idx : idx + 1
    } else {
      // Template drag — highlight folder
      dragOverFolderId.value = folderId
    }
  }

  function onDragLeaveSidebar() {
    dragOverFolderId.value = null
    folderDropIdx.value = -1
  }

  function onDropSidebar(folderId, idx, draggedIds) {
    if (dragType.value === 'folder' && draggingFolderIdx.value >= 0) {
      // Reorder folders
      let dropAt = folderDropIdx.value
      if (dropAt < 0) dropAt = idx
      const order = [...localFolderOrder.value]
      const [moved] = order.splice(draggingFolderIdx.value, 1)
      const insertAt = dropAt > draggingFolderIdx.value ? dropAt - 1 : dropAt
      order.splice(insertAt, 0, moved)
      localFolderOrder.value = order
      // Emit full order (including __default__ position) so parent can persist
      emit('reorder-folders', [...order])
    } else if (dragType.value === 'template' && draggedIds.length) {
      // Template dropped onto folder (null for default folder)
      const targetId = folderId === '__default__' ? null : folderId
      emit('move-templates', { templateIds: draggedIds, folderId: targetId })
      clearSelection()
    }
    onFolderDragEnd()
  }

  return {
    dragType,
    folderDropIdx,
    draggingFolderIdx,
    dragOverFolderId,
    onFolderDragStart,
    onFolderDragEnd,
    onDragOverSidebar,
    onDragLeaveSidebar,
    onDropSidebar,
  }
}
