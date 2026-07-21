/**
 * Folder Manager composable — folder CRUD logic, selection, inline editing,
 * and template drag/drop for ManageFoldersDialog.
 * Extracted from ManageFoldersDialog.vue
 */
import { ref, reactive, computed, watch, nextTick, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFolderDragReorder } from '@/composables/useFolderDragReorder'

export function useFolderManager(props, emit) {
  const { t } = useI18n()

  // Folder colors matching project palette
  const folderColors = [
    '#8B5CF6', '#3B82F6', '#10B981', '#F59E0B',
    '#EF4444', '#EC4899', '#06B6D4', '#6B7280',
  ]

  const selectedFolderId = ref('__default__')
  const editingId = ref(null)
  const editName = ref('')
  const editInput = ref(null)
  const selectedTemplateIds = reactive(new Set())
  const selectionMode = ref(false)
  const showMoveMenu = ref(false)

  // Inline delete confirm
  const deletingId = ref(null)

  // Default folder virtual object
  const defaultFolder = computed(() => ({
    id: '__default__',
    name: t('templateFolders.defaultFolder'),
    color: '#8B5CF6',
  }))

  // Local copy of folders for immediate reorder feedback (includes __default__)
  const localFolderOrder = ref([])
  watch([() => props.folders, () => props.defaultPosition], ([f, defPos]) => {
    const ids = f.map(x => x.id)
    const allIds = new Set(['__default__', ...ids])

    const existing = localFolderOrder.value.filter(id => allIds.has(id))
    if (existing.length === allIds.size) {
      const newIds = [...allIds].filter(id => !existing.includes(id))
      localFolderOrder.value = [...existing, ...newIds]
      return
    }

    const order = [...ids]
    const pos = Math.min(defPos ?? 0, order.length)
    order.splice(pos, 0, '__default__')
    localFolderOrder.value = order
  }, { immediate: true })

  // ---- Selection ----
  function clearSelection() {
    selectedTemplateIds.clear()
    selectionMode.value = false
  }

  // ---- Folder Drag Reorder (composable) ----
  const {
    dragType,
    folderDropIdx,
    draggingFolderIdx,
    dragOverFolderId,
    onFolderDragStart,
    onFolderDragEnd,
    onDragOverSidebar,
    onDragLeaveSidebar,
    onDropSidebar: dropSidebarHandler,
  } = useFolderDragReorder({ localFolderOrder, emit, clearSelection })

  const allSidebarFolders = computed(() => {
    const map = { '__default__': defaultFolder.value }
    for (const f of props.folders) map[f.id] = f
    return localFolderOrder.value.map(id => map[id]).filter(Boolean)
  })

  function getFolderCount(folder) {
    const folderId = folder.id === '__default__' ? null : folder.id
    return getTemplateCount(folderId)
  }

  // Inline new folder
  const creatingNew = ref(false)
  const newFolderName = ref('')
  const newFolderColor = ref('#8B5CF6')
  const newFolderInput = ref(null)

  onUnmounted(() => {
    document.body.style.overflow = ''
  })

  // Reset state when opened + lock body scroll
  watch(() => props.show, (v) => {
    if (v) {
      selectedFolderId.value = '__default__'
      cancelEdit()
      clearSelection()
      showMoveMenu.value = false
      deletingId.value = null
      cancelCreateFolder()
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  })

  const currentFolderName = computed(() => {
    if (selectedFolderId.value === '__default__') return t('templateFolders.defaultFolder')
    const f = props.folders.find(f => f.id === selectedFolderId.value)
    return f?.name || ''
  })

  const currentTemplates = computed(() => {
    return props.templates.filter(tpl => {
      const fid = tpl.folder_id || null
      if (selectedFolderId.value === '__default__') return !fid
      return fid === selectedFolderId.value
    })
  })

  function getTemplateCount(folderId) {
    return props.templates.filter(tpl => {
      const fid = tpl.folder_id || null
      return fid === folderId
    }).length
  }

  function selectFolder(id) {
    selectedFolderId.value = id
    clearSelection()
    showMoveMenu.value = false
  }

  // ---- Inline New Folder ----
  async function startCreateFolder() {
    creatingNew.value = true
    newFolderName.value = ''
    newFolderColor.value = '#8B5CF6'
    await nextTick()
    newFolderInput.value?.focus()
  }

  function cancelCreateFolder() {
    creatingNew.value = false
    newFolderName.value = ''
  }

  function confirmCreateFolder() {
    const name = newFolderName.value.trim()
    if (!name) return
    emit('create-folder', { name, color: newFolderColor.value })
    cancelCreateFolder()
  }

  // ---- Selection (handleItemClick) ----
  function handleItemClick(e, tpl) {
    const id = tpl.id || tpl.templateId
    if (selectionMode.value || e.metaKey || e.ctrlKey) {
      if (selectedTemplateIds.has(id)) {
        selectedTemplateIds.delete(id)
      } else {
        selectedTemplateIds.add(id)
      }
      selectionMode.value = true
    } else {
      selectedTemplateIds.clear()
      selectedTemplateIds.add(id)
      selectionMode.value = true
    }
  }

  // ---- Move ----
  function moveSelectedTo(folderId) {
    if (!selectedTemplateIds.size) return
    emit('move-templates', { templateIds: Array.from(selectedTemplateIds), folderId })
    clearSelection()
    showMoveMenu.value = false
  }

  // ---- Template Drag (grid -> sidebar folder) ----
  let draggedIds = []

  function onDragStart(e, tpl) {
    dragType.value = 'template'
    const id = tpl.id || tpl.templateId
    draggedIds = (selectedTemplateIds.has(id) && selectedTemplateIds.size > 1)
      ? Array.from(selectedTemplateIds)
      : [id]
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', draggedIds.join(','))
  }

  function onDragEnd() {
    draggedIds = []
    onFolderDragEnd()
  }

  function onDropSidebar(folderId, idx) {
    dropSidebarHandler(folderId, idx, draggedIds)
    draggedIds = []
  }

  // ---- Folder Rename ----
  async function startEdit(folder) {
    editingId.value = folder.id
    editName.value = folder.name
    await nextTick()
    editInput.value?.[0]?.focus()
  }

  function cancelEdit() {
    editingId.value = null
    editName.value = ''
  }

  function confirmRename(folder) {
    const name = editName.value.trim()
    if (!name || name === folder.name) {
      cancelEdit()
      return
    }
    emit('rename', { folder, name })
    cancelEdit()
  }

  function confirmDeleteFolder(folder) {
    deletingId.value = null
    emit('delete', folder)
  }

  return {
    // Constants
    folderColors,

    // State
    selectedFolderId,
    editingId,
    editName,
    editInput,
    selectedTemplateIds,
    selectionMode,
    showMoveMenu,
    deletingId,
    creatingNew,
    newFolderName,
    newFolderColor,
    newFolderInput,

    // Drag state
    dragType,
    folderDropIdx,
    draggingFolderIdx,
    dragOverFolderId,

    // Computed
    allSidebarFolders,
    currentFolderName,
    currentTemplates,

    // Methods
    clearSelection,
    getFolderCount,
    selectFolder,
    startCreateFolder,
    cancelCreateFolder,
    confirmCreateFolder,
    handleItemClick,
    moveSelectedTo,
    onDragStart,
    onDragEnd,
    onDropSidebar,
    onFolderDragStart,
    onFolderDragEnd,
    onDragOverSidebar,
    onDragLeaveSidebar,
    startEdit,
    cancelEdit,
    confirmRename,
    confirmDeleteFolder,
  }
}
