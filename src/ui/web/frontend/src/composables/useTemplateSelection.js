/**
 * useTemplateSelection
 * Batch selection logic for MyTemplates page
 */

import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'

export function useTemplateSelection(store) {
  const { t } = useI18n()
  const toast = useToast()

  const selectedIds = ref(new Set())
  const _selectionMode = ref(false)
  const isSelectionMode = computed(() => _selectionMode.value || selectedIds.value.size > 0)
  const batchDeleting = ref(false)
  const showBatchDeleteDialog = ref(false)

  function toggleSelect(item) {
    const id = item.templateId || item.id
    const newSet = new Set(selectedIds.value)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    selectedIds.value = newSet
  }

  function selectAll() {
    const ids = store.currentTemplates.map(t => t.templateId || t.id)
    selectedIds.value = new Set(ids)
  }

  function deselectAll() {
    selectedIds.value = new Set()
  }

  function enterSelectionMode() {
    _selectionMode.value = true
  }

  function cancel() {
    selectedIds.value = new Set()
    _selectionMode.value = false
  }

  function isSelected(item) {
    const id = item.templateId || item.id
    return selectedIds.value.has(id)
  }

  function handleBatchDelete() {
    if (selectedIds.value.size === 0) return
    showBatchDeleteDialog.value = true
  }

  async function confirmBatchDelete() {
    if (batchDeleting.value) return
    batchDeleting.value = true

    try {
      const ids = Array.from(selectedIds.value)
      let result

      // Split selected templates by source type
      const createdIds = []
      const installedIds = []
      for (const id of ids) {
        const tpl = store.allTemplates.find(t => (t.templateId || t.id) === id)
        if (tpl?._source === 'installed') {
          installedIds.push(id)
        } else {
          createdIds.push(id)
        }
      }
      // Delete in parallel
      const results = await Promise.all([
        createdIds.length ? store.batchDelete(createdIds) : { ok: true },
        installedIds.length ? store.batchRemove(installedIds) : { ok: true },
      ])
      result = {
        ok: results.every(r => r.ok),
        deleted: (results[0].deleted || 0) + (results[1].deleted || 0),
        failed: (results[0].failed || 0) + (results[1].failed || 0),
        error: results.find(r => !r.ok)?.error || null,
      }

      if (result.ok) {
        const deleted = result.deleted || 0
        const failed = result.failed || 0
        if (deleted > 0) {
          toast.success(t('myTemplates.batchDeleteSuccess', { count: deleted }))
        }
        if (failed > 0) {
          toast.error(t('myTemplates.batchDeleteFailed'))
        }
      } else {
        toast.error(result.error || t('myTemplates.batchDeleteFailed'))
      }

      selectedIds.value = new Set()
      await store.loadAll()
    } catch (err) {
      toast.error(err.message || t('myTemplates.batchDeleteFailed'))
    } finally {
      batchDeleting.value = false
      showBatchDeleteDialog.value = false
    }
  }

  function cancelBatchDelete() {
    showBatchDeleteDialog.value = false
  }

  return {
    selectedIds,
    isSelectionMode,
    batchDeleting,
    showBatchDeleteDialog,
    toggleSelect,
    enterSelectionMode,
    selectAll,
    deselectAll,
    cancel,
    isSelected,
    handleBatchDelete,
    confirmBatchDelete,
    cancelBatchDelete
  }
}
