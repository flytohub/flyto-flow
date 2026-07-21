/**
 * MyTemplates composable — data fetching, filtering, sorting, tag management,
 * and folder section computation extracted from MyTemplates.vue
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useMyTemplatesStore } from '@/stores/myTemplatesStore'
import { useUserStore } from '@/stores/userStore'
import { useTemplateActions } from '@/composables/useTemplateActions'
import { useTemplateSelection } from '@/composables/useTemplateSelection'
import { useToast } from '@/composables/useToast'
import { useTemplateFolders } from '@/composables/useTemplateFolders'
import { useJoinCollaboration } from '@/composables/useJoinCollaboration'
import { useWarroomRecipeBundleImport } from '@/composables/useWarroomRecipeBundleImport'
import { templatesAPI } from '@/api/templates'

export function useMyTemplates() {
  const { t } = useI18n()
  const router = useRouter()
  const store = useMyTemplatesStore()
  const userStore = useUserStore()
  const actions = useTemplateActions(store)
  const selection = useTemplateSelection(store)

  const toast = useToast()
  const folderActions = useTemplateFolders()
  const joinCollab = useJoinCollaboration({ router, t })
  const warroomImport = useWarroomRecipeBundleImport(store)
  const viewMode = ref('grid')

  // Submit PR dialog state
  const showPRForm = ref(false)
  const prFormTarget = ref(null)
  const prSubmitting = ref(false)

  // YAML import
  const yamlFileInput = ref(null)

  function triggerImportYAML() {
    yamlFileInput.value?.click()
  }

  async function handleImportYAML(event) {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const yamlContent = await file.text()
      const result = await templatesAPI.importYAML(yamlContent)
      if (!result.ok) {
        toast.error(result.error || t('common.error'))
        return
      }
      toast.success(t('myTemplates.importSuccess', 'Template imported'))
      store.fetchCreated()
      if (result.template?.id) {
        router.push(`/templates/${result.template.id}`)
      }
    } catch (err) {
      toast.error(err.message || t('common.error'))
    } finally {
      if (yamlFileInput.value) yamlFileInput.value.value = ''
    }
  }

  // Tag filtering
  const selectedTags = ref([])
  const availableTags = ref([])

  async function fetchAvailableTags() {
    availableTags.value = await templatesAPI.getAvailableTags()
  }

  const filteredTemplates = computed(() => {
    if (!selectedTags.value.length) return store.allTemplates
    return store.allTemplates.filter(tpl =>
      selectedTags.value.some(tag => (tpl.tags || []).includes(tag))
    )
  })

  function toggleTagFilter(tag) {
    const idx = selectedTags.value.indexOf(tag)
    if (idx === -1) {
      selectedTags.value.push(tag)
    } else {
      selectedTags.value.splice(idx, 1)
    }
  }

  // Legacy compat: folderSections no longer used in File Manager mode
  const folderSections = computed(() => [])

  // Submit PR flow
  function openPRForm(templateItem) {
    prFormTarget.value = templateItem
    showPRForm.value = true
  }

  async function handleSubmitPR(data) {
    if (!prFormTarget.value) return
    const sourceTemplateId = prFormTarget.value.sourceTemplateId || prFormTarget.value.forkContext?.sourceTemplateId
    if (!sourceTemplateId) {
      toast.error(t('common.error'))
      return
    }
    prSubmitting.value = true
    try {
      const result = await templatesAPI.createPullRequest(sourceTemplateId, {
        forkId: data.forkId,
        title: data.title,
        description: data.description,
      })
      if (result.ok) {
        toast.success(t('templateCollaboration.pullRequests.created'))
        showPRForm.value = false
        prFormTarget.value = null
      } else {
        toast.error(result.error || t('common.error'))
      }
    } catch (err) {
      toast.error(err.message || t('common.error'))
    } finally {
      prSubmitting.value = false
    }
  }

  // Folder action handlers
  function handleFolderRename(folder) {
    folderActions.openRenameFolder(folder)
  }

  function handleFolderDelete(folder) {
    folderActions.openDeleteFolder(folder)
  }

  async function handleManageFolderRename({ folder, name }) {
    try {
      const result = await templatesAPI.updateFolder(folder.id, { name })
      if (result?.ok) {
        await store.fetchFolders()
      } else {
        toast.error(result?.error || t('common.error'))
      }
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function handleFinderMoveTemplates({ templateIds, folderId }) {
    try {
      const result = await store.moveTemplates(templateIds, folderId)
      if (result?.ok) {
        toast.success(t('templateFolders.moveSuccess'))
      } else {
        toast.error(result?.error || t('common.error'))
      }
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function handleFinderDeleteFolder(folder) {
    try {
      const result = await store.deleteFolder(folder.id)
      if (result?.ok) {
        toast.success(t('templateFolders.deleteSuccess'))
        await Promise.all([store.fetchCreated(), store.fetchInstalled()])
      } else {
        toast.error(result?.error || t('common.error'))
      }
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function handleReorderFolders(fullOrder) {
    const defaultPos = fullOrder.indexOf('__default__')
    const realIds = fullOrder.filter(id => id !== '__default__')
    try {
      await templatesAPI.reorderFolders(realIds, defaultPos >= 0 ? defaultPos : 0)
      await store.fetchFolders()
    } catch (err) {
      toast.error(err.message)
    }
  }

  async function handleManageDialogClose() {
    folderActions.showManageFoldersDialog.value = false
    await store.fetchFolders()
  }

  async function openManageDialog() {
    folderActions.showManageFoldersDialog.value = true
    await store.fetchAllTemplatesFull()
  }

  // Debounced search
  let searchTimer = null
  watch(() => store.searchQuery, () => {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      store.fetchTemplates(true)
    }, 300)
  })

  watch(() => store.sortBy, () => {
    store.fetchTemplates(true)
  })

  // Close context menu on click outside
  function handleClickOutside(e) {
    if (actions.openMenuId.value && !e.target.closest('.relative')) {
      actions.openMenuId.value = null
    }
  }

  watch(() => store.allTemplates, () => {
    fetchAvailableTags()
  })

  onMounted(async () => {
    await userStore.waitForAuth()
    await store.loadAll()
    fetchAvailableTags()
    document.addEventListener('click', handleClickOutside)
  })

  onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
    clearTimeout(searchTimer)
  })

  return {
    // Stores
    store,
    actions,
    selection,
    folderActions,
    joinCollab,
    warroomImport,

    // State
    viewMode,
    showPRForm,
    prFormTarget,
    prSubmitting,
    yamlFileInput,
    selectedTags,
    availableTags,

    // Computed
    folderSections,

    // Methods
    triggerImportYAML,
    handleImportYAML,
    toggleTagFilter,
    openPRForm,
    handleSubmitPR,
    handleFolderRename,
    handleFolderDelete,
    handleManageFolderRename,
    handleFinderMoveTemplates,
    handleFinderDeleteFolder,
    handleReorderFolders,
    handleManageDialogClose,
    openManageDialog,
  }
}
