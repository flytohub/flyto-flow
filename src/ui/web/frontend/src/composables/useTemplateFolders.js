/**
 * Template Folders Composable
 * Manages folder dialog states and actions
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMyTemplatesStore } from '@/stores/myTemplatesStore'
import { useToast } from '@/composables/useToast'

export function useTemplateFolders() {
  const { t } = useI18n()
  const store = useMyTemplatesStore()
  const toast = useToast()

  // Create folder dialog
  const showCreateFolderDialog = ref(false)
  const creatingFolder = ref(false)

  // Rename folder dialog
  const showRenameFolderDialog = ref(false)
  const renameTarget = ref(null)
  const renameFolderName = ref('')
  const renamingFolder = ref(false)

  // Delete folder dialog
  const showDeleteFolderDialog = ref(false)
  const deleteTarget = ref(null)
  const deletingFolder = ref(false)

  // Move to folder dialog
  const showMoveToFolderDialog = ref(false)
  const moveTargetIds = ref([])

  // Manage folders dialog
  const showManageFoldersDialog = ref(false)

  async function handleCreateFolder({ name, color }) {
    if (!name) return
    creatingFolder.value = true
    try {
      const result = await store.createFolder({
        name,
        color,
        tab: 'created',
        parent_id: null,
      })
      if (result?.ok) {
        toast.success(t('templateFolders.createSuccess'))
        showCreateFolderDialog.value = false
      } else {
        toast.error(result?.error || t('common.error'))
      }
    } catch (err) {
      toast.error(err.message)
    } finally {
      creatingFolder.value = false
    }
  }

  function openRenameFolder(folder) {
    renameTarget.value = folder
    renameFolderName.value = folder.name
    showRenameFolderDialog.value = true
  }

  async function handleRenameFolder() {
    if (!renameTarget.value || !renameFolderName.value.trim()) return
    renamingFolder.value = true
    try {
      const { templatesAPI } = await import('@/api/templates')
      const result = await templatesAPI.updateFolder(renameTarget.value.id, {
        name: renameFolderName.value.trim()
      })
      if (result?.ok) {
        await store.fetchFolders()
        showRenameFolderDialog.value = false
        renameTarget.value = null
      } else {
        toast.error(result?.error || t('common.error'))
      }
    } catch (err) {
      toast.error(err.message)
    } finally {
      renamingFolder.value = false
    }
  }

  function openDeleteFolder(folder) {
    deleteTarget.value = folder
    showDeleteFolderDialog.value = true
  }

  async function handleDeleteFolder() {
    if (!deleteTarget.value) return
    deletingFolder.value = true
    try {
      const result = await store.deleteFolder(deleteTarget.value.id)
      if (result?.ok) {
        toast.success(t('templateFolders.deleteSuccess'))
        showDeleteFolderDialog.value = false
        deleteTarget.value = null
        // Re-fetch templates since they moved to root
        await Promise.all([store.fetchCreated(), store.fetchInstalled()])
      } else {
        toast.error(result?.error || t('common.error'))
      }
    } catch (err) {
      toast.error(err.message)
    } finally {
      deletingFolder.value = false
    }
  }

  function openMoveToFolder(ids) {
    moveTargetIds.value = Array.isArray(ids) ? ids : [ids]
    showMoveToFolderDialog.value = true
  }

  async function handleMoveToFolder(folderId) {
    try {
      const result = await store.moveTemplates(moveTargetIds.value, folderId)
      if (result?.ok) {
        toast.success(t('templateFolders.moveSuccess'))
        showMoveToFolderDialog.value = false
        moveTargetIds.value = []
      } else {
        toast.error(result?.error || t('common.error'))
      }
    } catch (err) {
      toast.error(err.message)
    }
  }

  return {
    // Create
    showCreateFolderDialog,
    creatingFolder,
    handleCreateFolder,
    // Rename
    showRenameFolderDialog,
    renameTarget,
    renameFolderName,
    renamingFolder,
    openRenameFolder,
    handleRenameFolder,
    // Delete
    showDeleteFolderDialog,
    deleteTarget,
    deletingFolder,
    openDeleteFolder,
    handleDeleteFolder,
    // Move
    showMoveToFolderDialog,
    moveTargetIds,
    openMoveToFolder,
    handleMoveToFolder,
    // Manage dialog
    showManageFoldersDialog,
  }
}
