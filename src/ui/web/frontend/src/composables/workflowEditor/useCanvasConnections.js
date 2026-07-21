/**
 * Canvas Connections Composable
 *
 * Handles connection creation, validation (handleConnect),
 * switch case selection, and edge management.
 */
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { validateConnection as validateConnectionApi } from '../../api/modules'
import { useModulesStore } from '../../stores/modulesStore'
import {
  createEdge,
  isMultiOutputNode,
} from './useCanvasOperations'
import { getEdgeColorForSourceHandle } from './workflowConstants/edgeConstants'
import { CASE_COLORS } from '../../config/nodeTypes/SwitchNode'
import { isSwitchNode } from '@/services/nodeService'
import { useToast } from '../useToast'
import { trackBuilder } from '@/utils/telemetry/builderTracker'

export function useCanvasConnections({ nodes, edges, saveHistoryState, syncToParent, HISTORY_ACTIONS }) {
  const { t } = useI18n()
  const toast = useToast()
  const modulesStore = useModulesStore()

  // Switch case selector state
  const showCaseSelector = ref(false)
  const pendingCaseSelection = ref(null)
  const pendingCaseOptions = ref([])

  function isValidConnection(connection) {
    if (connection.source === connection.target) {
      toast.warning(t('workflow.validation.selfConnection'))
      return false
    }

    const sourceNode = nodes.value.find(n => n.id === connection.source)
    const targetNode = nodes.value.find(n => n.id === connection.target)

    if (!sourceNode || !targetNode) return false

    return true
  }

  async function handleConnect(params) {
    const sourceNode = nodes.value.find(n => n.id === params.source)
    const targetNode = nodes.value.find(n => n.id === params.target)

    const sourceModuleId = sourceNode?.data?.module
    const targetModuleId = targetNode?.data?.module
    if (!sourceModuleId || !targetModuleId) {
      toast.warning(t('workflow.validation.missingModule'))
      return
    }

    try {
      const result = await validateConnectionApi(
        sourceModuleId,
        targetModuleId,
        params.sourceHandle || null,
        params.targetHandle || null
      )
      if (!result?.valid) {
        const sourceLabel = modulesStore.modulesMetadata[sourceModuleId]?.label || sourceModuleId
        const targetLabel = modulesStore.modulesMetadata[targetModuleId]?.label || targetModuleId

        const errorCode = result?.error_code
        const meta = result?.meta || {}

        let errorMessage
        switch (errorCode) {
          case 'TYPE_MISMATCH':
            errorMessage = t('workflow.validation.typeMismatch', {
              to_module: targetLabel,
              expected: meta.expected || 'unknown',
              received: meta.received || 'unknown'
            })
            break
          case 'INCOMPATIBLE_MODULES':
            errorMessage = t('workflow.validation.incompatibleModules', {
              source: sourceLabel,
              target: targetLabel
            })
            break
          case 'SELF_CONNECTION':
            errorMessage = t('workflow.validation.selfConnection')
            break
          case 'MAX_CONNECTIONS':
            errorMessage = t('workflow.validation.maxConnections', {
              port: meta.port || 'input'
            })
            break
          case 'INVALID_PORT':
            errorMessage = t('workflow.validation.invalidPort', {
              port: meta.port || 'unknown'
            })
            break
          default:
            errorMessage = result?.reason || t('workflow.validation.incompatibleModules', {
              source: sourceLabel,
              target: targetLabel
            })
        }

        toast.warning(errorMessage)
        return
      }
    } catch (error) {
      toast.warning(t('workflow.validation.apiError', 'Connection validation failed'))
      return
    }

    if (!isMultiOutputNode(sourceModuleId, modulesStore) && sourceNode) {
      const outgoing = edges.value.filter(edge => edge.source === sourceNode.id)
      if (outgoing.length > 0) {
        toast.warning(t('workflow.validation.multiOutputRecommended'))
      }
    }

    // Switch nodes: if dragging from generic cases handle, require case selection
    const cases = sourceNode?.data?.params?.cases || []
    if (isSwitchNode(sourceModuleId, modulesStore) && params.sourceHandle === 'source-cases') {
      if (cases.length === 1 && cases[0]?.id) {
        params.sourceHandle = `source-case-${cases[0].id}`
        params.data = { caseId: cases[0].id }
      } else if (cases.length > 1) {
        pendingCaseSelection.value = { params, sourceNode, targetNode }
        pendingCaseOptions.value = cases
        showCaseSelector.value = true
        return
      }
    }

    saveHistoryState(HISTORY_ACTIONS.EDGE_ADD, { source: params.source, target: params.target })

    const edgeColor = getEdgeColorForSourceHandle(params.sourceHandle, sourceNode, CASE_COLORS)
    const edgeOpts = edgeColor ? { color: edgeColor } : {}
    const edge = createEdge(params.source, params.target, params.sourceHandle, params.targetHandle, {
      ...edgeOpts,
      sourceNodeData: sourceNode?.data,
      data: params.data || undefined
    })
    edges.value = [...edges.value, edge]

    const sourceType = sourceNode?.data?.module || 'unknown'
    const targetType = targetNode?.data?.module || 'unknown'
    trackBuilder.edgeCreate(sourceType, targetType)

    syncToParent()
  }

  function confirmCaseSelection(caseItem) {
    if (!pendingCaseSelection.value) return
    const { params, sourceNode } = pendingCaseSelection.value
    const caseId = caseItem?.id
    if (!caseId) {
      cancelCaseSelection()
      return
    }

    const resolvedParams = {
      ...params,
      sourceHandle: `source-case-${caseId}`,
      data: { caseId }
    }

    saveHistoryState(HISTORY_ACTIONS.EDGE_ADD, { source: resolvedParams.source, target: resolvedParams.target })

    const edgeColor = getEdgeColorForSourceHandle(resolvedParams.sourceHandle, sourceNode, CASE_COLORS)
    const edgeOpts = edgeColor ? { color: edgeColor } : {}
    const edge = createEdge(resolvedParams.source, resolvedParams.target, resolvedParams.sourceHandle, resolvedParams.targetHandle, {
      ...edgeOpts,
      sourceNodeData: sourceNode?.data,
      data: resolvedParams.data
    })
    edges.value = [...edges.value, edge]

    showCaseSelector.value = false
    pendingCaseSelection.value = null
    pendingCaseOptions.value = []
    syncToParent()
  }

  function cancelCaseSelection() {
    showCaseSelector.value = false
    pendingCaseSelection.value = null
    pendingCaseOptions.value = []
  }

  return {
    showCaseSelector,
    pendingCaseOptions,
    isValidConnection,
    handleConnect,
    confirmCaseSelection,
    cancelCaseSelection
  }
}
