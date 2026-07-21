/**
 * Canvas Dialogs Composable
 *
 * Manages state for canvas dialogs: node search, note edit modal.
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from '../useToast'

export function useCanvasDialogs({ nodes, syncToParent, saveHistoryState, HISTORY_ACTIONS }) {
  const { t } = useI18n()
  const toast = useToast()

  // Node search dialog
  const showNodeSearch = ref(false)

  // Note edit modal
  const showNoteModal = ref(false)
  const noteModalNodeId = ref(null)
  const noteModalInitialValue = ref('')

  function handleEditNote(nodeId) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (!node) return

    noteModalNodeId.value = nodeId
    noteModalInitialValue.value = node.data?.description || ''
    showNoteModal.value = true
  }

  function handleNoteSave(descriptionText) {
    const nodeId = noteModalNodeId.value
    const node = nodes.value.find(n => n.id === nodeId)
    if (!node) {
      showNoteModal.value = false
      return
    }

    saveHistoryState(HISTORY_ACTIONS.NODE_UPDATE, { nodeId, field: 'description' })

    if (!node.data) node.data = {}
    node.data.description = descriptionText

    syncToParent()
    showNoteModal.value = false

    if (descriptionText) {
      toast.success(t('workflow.descriptionSaved', 'Description saved'))
    } else {
      toast.info(t('workflow.descriptionRemoved', 'Description removed'))
    }
  }

  function handleNoteDelete() {
    handleNoteSave('')
  }

  return {
    showNodeSearch,
    showNoteModal,
    noteModalNodeId,
    noteModalInitialValue,
    handleEditNote,
    handleNoteSave,
    handleNoteDelete
  }
}
