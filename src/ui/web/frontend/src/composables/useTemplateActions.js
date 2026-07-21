/**
 * useTemplateActions
 * Extracts all template CRUD / action logic from MyTemplates.vue
 */

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { templatesAPI } from '@/api/templates'
import { useToast } from '@/composables/useToast'
import { useModulesStore } from '@/stores/modulesStore'

export function useTemplateActions(store) {
  const router = useRouter()
  const { t } = useI18n()
  const toast = useToast()

  // Modal / dialog state
  const showCreateModal = ref(false)
  const showEditModal = ref(false)
  const editTarget = ref(null)
  const showDeleteDialog = ref(false)
  const deleteTarget = ref(null)
  const showPublishModal = ref(false)
  const publishTarget = ref(null)
  const showKeyManager = ref(false)
  const keyManagerTarget = ref(null)
  const openMenuId = ref(null)
  const duplicating = ref(false)
  const deleting = ref(false)

  // Publish success state
  const publishSuccessMessage = ref('')
  const publishedInviteKey = ref('')
  const copiedKey = ref(false)

  // ---------- CRUD ----------

  function createTemplate() {
    showCreateModal.value = true
  }

  function onTemplateCreated(templateId) {
    router.push(`/templates/builder/${templateId}`)
  }

  function openTemplate(item) {
    const id = item.templateId || item.id
    router.push(`/templates/builder/${id}`)
  }

  function editTemplate(item) {
    openMenuId.value = null
    editTarget.value = item
    showEditModal.value = true
  }

  function onTemplateUpdated() {
    store.loadAll()
  }

  function runTemplate(item) {
    openMenuId.value = null
    const id = item.templateId || item.id
    router.push(`/templates/builder/${id}?mode=preview`)
  }

  async function shareTemplate(item) {
    openMenuId.value = null
    const id = item.templateId || item.id
    const url = `${window.location.origin}/templates/${id}`
    try {
      await navigator.clipboard.writeText(url)
      toast.success(t('common.linkCopied'))
    } catch {
      toast.error(t('common.error'))
    }
  }

  async function duplicateTemplate(item) {
    openMenuId.value = null
    if (duplicating.value) return

    duplicating.value = true
    try {
      const id = item.templateId || item.id
      await templatesAPI.addToLibrary(id)
      await store.loadAll()
      useModulesStore().clearCache()
      toast.success(t('myTemplates.addToLibrarySuccess'))
    } catch {
      toast.error(t('myTemplates.addToLibraryFailed'))
    } finally {
      duplicating.value = false
    }
  }

  function deleteTemplate(item) {
    openMenuId.value = null
    deleteTarget.value = item
    showDeleteDialog.value = true
  }

  async function confirmDelete() {
    if (!deleteTarget.value || deleting.value) return

    deleting.value = true
    try {
      const isInstalled = deleteTarget.value._source === 'installed'
      if (isInstalled) {
        const result = await templatesAPI.removeFromLibrary(deleteTarget.value.templateId)
        if (!result.ok) throw new Error(result.error || 'Remove failed')
      } else {
        const result = await templatesAPI.deleteTemplate(deleteTarget.value.id)
        if (!result.ok) throw new Error(result.error || 'Delete failed')
      }
      await store.loadAll()
      useModulesStore().clearCache()
      toast.success(t('myTemplates.deleteSuccess'))
    } catch (err) {
      toast.error(err.message || t('myTemplates.deleteFailed'))
    } finally {
      deleting.value = false
      showDeleteDialog.value = false
      deleteTarget.value = null
    }
  }

  function cancelDelete() {
    showDeleteDialog.value = false
    deleteTarget.value = null
  }

  // ---------- Publish ----------

  function publishTemplate(item) {
    openMenuId.value = null
    const templateId = item.templateId || item.id
    router.push(`/templates/${templateId}/publish`)
  }

  function onTemplatePublished(result) {
    if (result.inviteKey) {
      const keyCode = result.inviteKey.key || result.inviteKey
      publishedInviteKey.value = keyCode
      publishSuccessMessage.value = ''
    } else {
      publishSuccessMessage.value = t('publish.publishSuccess')
      publishedInviteKey.value = ''
    }

    setTimeout(() => {
      publishSuccessMessage.value = ''
      publishedInviteKey.value = ''
      copiedKey.value = false
    }, 10000)

    store.loadAll()
  }

  function copyInviteKey() {
    if (!publishedInviteKey.value) return
    navigator.clipboard.writeText(publishedInviteKey.value).then(() => {
      copiedKey.value = true
      setTimeout(() => { copiedKey.value = false }, 2000)
    }).catch(() => {})
  }

  function manageKeys(item) {
    openMenuId.value = null
    keyManagerTarget.value = item
    showKeyManager.value = true
  }

  // ---------- Fork / Sync / AutoUpdate ----------

  async function forkTemplate(item) {
    openMenuId.value = null
    const templateId = item.templateId || item.id
    const purchaseId = item.purchaseId || item.purchaseContext?.purchaseId

    try {
      const result = await templatesAPI.forkTemplate(templateId, purchaseId)
      if (result.ok) {
        toast.success(t('myTemplates.forkSuccess'))
        await store.loadAll()
        useModulesStore().clearCache()
      } else {
        toast.error(result.error || t('myTemplates.forkFailed'))
      }
    } catch {
      toast.error(t('myTemplates.forkFailed'))
    }
  }

  async function syncTemplate(item) {
    openMenuId.value = null
    const purchaseId = item.purchaseId || item.purchaseContext?.purchaseId

    if (!purchaseId) {
      toast.error(t('myTemplates.syncFailed'))
      return
    }

    try {
      const result = await templatesAPI.syncPurchase(purchaseId)
      if (result.ok) {
        toast.success(t('myTemplates.syncSuccess'))
        await store.loadAll()
      } else {
        toast.error(result.error || t('myTemplates.syncFailed'))
      }
    } catch {
      toast.error(t('myTemplates.syncFailed'))
    }
  }

  async function handleUpdateAutoUpdate(item, value) {
    openMenuId.value = null
    const purchaseId = item.purchaseId || item.purchaseContext?.purchaseId

    if (!purchaseId) {
      toast.error(t('myTemplates.updateSettingsFailed'))
      return
    }

    try {
      const result = await templatesAPI.updateLibrarySettings(purchaseId, { autoUpdate: value })
      if (result.ok) {
        if (item.purchaseContext) {
          item.purchaseContext.autoUpdate = value
        } else {
          item.autoUpdate = value
        }
        toast.success(t('myTemplates.updateSettingsSuccess'))
      } else {
        toast.error(result.error || t('myTemplates.updateSettingsFailed'))
      }
    } catch {
      toast.error(t('myTemplates.updateSettingsFailed'))
    }
  }

  // ---------- Misc ----------

  function toggleMenu(id) {
    openMenuId.value = openMenuId.value === id ? null : id
  }

  function goToMarketplace() {
    router.push('/marketplace')
  }

  return {
    // Modal state
    showCreateModal,
    showEditModal,
    editTarget,
    showDeleteDialog,
    deleteTarget,
    showPublishModal,
    publishTarget,
    showKeyManager,
    keyManagerTarget,
    openMenuId,
    duplicating,
    deleting,
    // Publish toast state
    publishSuccessMessage,
    publishedInviteKey,
    copiedKey,
    // Actions
    createTemplate,
    onTemplateCreated,
    openTemplate,
    editTemplate,
    onTemplateUpdated,
    runTemplate,
    shareTemplate,
    duplicateTemplate,
    deleteTemplate,
    confirmDelete,
    cancelDelete,
    publishTemplate,
    onTemplatePublished,
    copyInviteKey,
    manageKeys,
    forkTemplate,
    syncTemplate,
    handleUpdateAutoUpdate,
    toggleMenu,
    goToMarketplace
  }
}
