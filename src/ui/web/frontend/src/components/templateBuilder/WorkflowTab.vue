<template>
    <div class="workflow-tab-container">
        <div class="workflow-canvas-wrapper">
            <WorkflowCanvas
                ref="workflowCanvasRef"
                :elements="elements"
                :default-modules="defaultModules"
                :expert-modules="expertModules"
                :selected-node-id="selectedNodeSafe?.id"
                :debug-mode="debugMode"
                :debug-selected-nodes="debugSelectedNodeIds"
                :execution-node-states="executionNodeStates"
                :agent-activity="agentActivity"
                :checkpoints="checkpoints"
                :can-use-checkpoint="canUseCheckpoint"
                :can-use-data-pinning="canUseDataPinning"
                :execution-status="executionStatus"
                :control-loading="controlLoading"
                :saved-viewport="savedViewport"
                @update:elements="dispatch({ type: 'CANVAS_SET_ELEMENTS', next: $event })"
                @update:viewport="$emit('update:viewport', $event)"
                @node-click="$emit('node-click', $event)"
                @drop="$emit('drop', $event)"
                @dragover="$emit('dragover', $event)"
                @add-first-node="$emit('add-first-node')"
                @delete-node="$emit('delete-node', $event)"
                @debug-selection-change="$emit('debug-selection-change', $event)"
                @toggle-checkpoint="$emit('toggle-checkpoint', $event)"
                @pause-execution="$emit('pause-execution')"
                @resume-execution="$emit('resume-execution')"
                @step-execution="$emit('step-execution')"
                @stop-execution="$emit('stop-execution')"
                @run-to-end="$emit('run-to-end')"
                @edit-container="$emit('edit-container', $event)"
                @retry-node="$emit('retry-node', $event)"
                @create-template="$emit('create-template')"
                @edit-template="$emit('edit-template', $event)"
            />
        </div>

        <div v-if="!debugMode" class="node-properties-panel" :class="{ collapsed }">
            <CollapseHandle :collapsed="collapsed" @toggle="$emit('toggle-collapsed')" />

            <div class="panel-content" :class="{ hidden: collapsed }">
                <PanelHeader :title="t('templateBuilder.nodeProperties.title')" />

                <div v-if="selectedNodeSafe" class="panel-body custom-scrollbar">
                    <div v-if="readOnly" class="read-only-banner">
                        <Lock :size="14" />
                        <span>{{ t('templateBuilder.nodeProperties.readOnlyMode') }}</span>
                    </div>

                    <NodeBasicInfo :nodeId="selectedNodeSafe.id" :module="selectedNodeSafe.data.module" />

                    <NodeDescription
                        :model-value="selectedNodeSafe.data.description"
                        :read-only="readOnly"
                        @update:model-value="updateDescription"
                    />

                    <div class="panel-divider"></div>

                    <!-- Parameters - 動態載入元件（後端為唯一真相源） -->
                    <div class="prop-group">
                        <component
                            v-if="paramsComponent"
                            :is="paramsComponent"
                            :module-id="selectedNodeSafe.data.module"
                            :moduleType="selectedNodeSafe.data.module"
                            :params="selectedNodeSafe.data.params"
                            :connections="selectedNodeSafe.data.connections"
                            :schema="moduleSchema"
                            :read-only="readOnly"
                            :ui-input-fields="effectiveUiInputFields"
                            :previous-steps="previousSteps"
                            @update:params="updateParams"
                            @update:connections="updateConnections"
                        />
                    </div>

                    <!-- Trigger Config (schedule/webhook/event settings) -->
                    <TriggerConfigPanel
                        v-if="isSelectedTrigger && !readOnly"
                        :params="selectedNodeSafe.data.params || {}"
                        :webhook-id="selectedNodeSafe.data.params?.webhook_id"
                        :read-only="readOnly"
                        @update:params="updateParams"
                        @test-webhook="$emit('test-webhook', $event)"
                    />

                    <div class="panel-divider"></div>

                    <!-- Preview action buttons -->
                    <div v-if="hasNodeOutput" class="panel-actions">
                        <button
                            v-if="hasNodeOutput"
                            class="preview-results-btn"
                            @click="showResultDialog = true"
                        >
                            <Eye :size="14" />
                            Preview Results
                        </button>
                    </div>

                    <NodeExecutionSettings
                        :node="selectedNodeSafe"
                        :read-only="readOnly"
                        @update:node="updateNodeData"
                        @update:settings="updateNodeData"
                    />
                </div>

                <div v-if="selectedNodeSafe && !readOnly" class="panel-sticky-footer">
                    <DeleteNodeButton @delete="$emit('delete-selected-node')" />
                </div>

                <EmptyPropertiesPanel v-if="!selectedNodeSafe" />
            </div>
        </div>

        <!-- Execution Detail Dialog -->
        <ExecutionDetailDialog
            :show="showResultDialog"
            :label="selectedNodeSafe?.data?.module || ''"
            :duration="selectedNodeDuration"
            :node-output="selectedNodeOutput"
            :node-input="selectedNodeInput"
            :node-error="selectedNodeError"
            :display-outputs="selectedNodeDisplayOutputs"
            @close="showResultDialog = false"
        />
    </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import WorkflowCanvas from '../WorkflowCanvas.vue'
import CollapseHandle from './CollapseHandle.vue'
import PanelHeader from './PanelHeader.vue'
import NodeBasicInfo from './NodeBasicInfo.vue'
import NodeDescription from './NodeDescription.vue'
// Use simplified execution settings - collapsed by default
import NodeExecutionSettings from './NodeExecutionSettingsSimplified.vue'
// 動態參數元件載入（後端為唯一真相源）
import { getParamsComponentForModule } from './params/ParamsComponentRegistry'
import DeleteNodeButton from './DeleteNodeButton.vue'
import EmptyPropertiesPanel from './EmptyPropertiesPanel.vue'
import TriggerConfigPanel from '../triggers/TriggerConfigPanel.vue'
import { Settings, Lock, Eye } from 'lucide-vue-next'
import { useModulesStore } from '@/stores/modulesStore'
import { isTriggerNode } from '@/services/nodeService'
import { useNodeOutputStore } from '@/stores/execution/nodeOutputStore'
import ExecutionDetailDialog from '../workflowCanvas/nodes/ExecutionDetailDialog.vue'

const { t } = useI18n()

// Ref to WorkflowCanvas for autoLayout
const workflowCanvasRef = ref(null)

const props = defineProps({
    elements: { type: Array, required: true },
    selectedNode: { type: Object, default: null },
    defaultModules: { type: Array, default: () => [] },
    expertModules: { type: Array, default: () => [] },
    debugMode: { type: Boolean, default: false },
    debugSelectedNodeIds: { type: Array, default: () => [] },
    // Backend-computed node states (S-Grade: nodeId -> 'pending'|'running'|'completed'|'failed')
    executionNodeStates: { type: Object, default: () => ({}) },
    agentActivity: { type: Object, default: () => ({}) },
    collapsed: { type: Boolean, default: false },
    uiInputFields: { type: Array, default: () => [] },
    previousSteps: { type: Array, default: () => [] },
    readOnly: { type: Boolean, default: false },
    checkpoints: { type: Array, default: () => [] },
    canUseCheckpoint: { type: Boolean, default: false },
    canUseDataPinning: { type: Boolean, default: false },
    executionStatus: { type: String, default: 'idle' },
    controlLoading: { type: Boolean, default: false },
    savedViewport: { type: Object, default: null },
    enableHistory: { type: Boolean, default: true },
    historyLimit: { type: Number, default: 200 },
    debounceMs: { type: Number, default: 120 },
    groupMs: { type: Number, default: 800 },
    enableHotkeys: { type: Boolean, default: true }
})

const emit = defineEmits([
    'update:elements',
    'update:viewport',
    'node-click',
    'drop',
    'dragover',
    'add-first-node',
    'delete-node',
    'debug-selection-change',
    'toggle-collapsed',
    'delete-selected-node',
    'toggle-checkpoint',
    'resume-execution',
    'run-to-end',
    'edit-container',
    'retry-node',
    'history:can-undo',
    'history:can-redo',
    'history:undo',
    'history:redo',
    'test-webhook',
    'create-template',
    'edit-template'
])

const selectedNodeId = computed(() => props.selectedNode?.id || '')

const selectedNodeSafe = computed(() => {
    if (!selectedNodeId.value) return null
    return props.elements.find(el => el?.id === selectedNodeId.value && el?.data) || null
})

const modulesStore = useModulesStore()
const nodeOutputStore = useNodeOutputStore()

const showResultDialog = ref(false)

const selectedNodeOutput = computed(() => {
    const id = selectedNodeId.value
    return id ? nodeOutputStore.getNodeOutput(id) : null
})

const selectedNodeInput = computed(() => {
    const id = selectedNodeId.value
    return id ? nodeOutputStore.getNodeInputs(id) : null
})

const selectedNodeError = computed(() => {
    const id = selectedNodeId.value
    return id ? nodeOutputStore.getNodeError(id) : null
})

const selectedNodeDisplayOutputs = computed(() => {
    const id = selectedNodeId.value
    return id ? nodeOutputStore.getNodeDisplayOutputs(id) : []
})

const selectedNodeDuration = computed(() => {
    const id = selectedNodeId.value
    if (!id) return ''
    const ms = nodeOutputStore.getNodeDuration(id)
    if (ms === null || ms === undefined) return ''
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
})

const hasNodeOutput = computed(() => {
    const id = selectedNodeId.value
    if (!id) return false
    // Show Preview Results if node was executed (has any record), has error, or has display outputs
    return nodeOutputStore.hasOutput(id) || !!selectedNodeDisplayOutputs.value?.length
})

const moduleSchema = computed(() => {
    const moduleId = selectedNodeSafe.value?.data?.module
    if (!moduleId) return null
    return modulesStore.modulesMetadata?.[moduleId]?.paramsSchema || null
})

// 動態取得參數元件 - 所有模組都一樣
const paramsComponent = computed(() => {
    if (!selectedNodeSafe.value) return null

    const moduleId = selectedNodeSafe.value.data?.module
    if (!moduleId) return null

    // 從 modulesMetadata 取得 - 跟普通模組一樣
    const metadata = modulesStore.modulesMetadata?.[moduleId]

    return getParamsComponentForModule({
        ...metadata,
        module_id: moduleId
    }, modulesStore)
})

const canEdit = computed(() => !props.readOnly && props.executionStatus !== 'running' && !props.controlLoading)

const isSelectedTrigger = computed(() => {
    const moduleId = selectedNodeSafe.value?.data?.module
    return moduleId ? isTriggerNode(moduleId, modulesStore) : false
})

// UI input fields for variable suggestions
// template.invoke nodes should NOT see parent template's UI inputs
const effectiveUiInputFields = computed(() => {
    const moduleId = selectedNodeSafe.value?.data?.module
    if (moduleId?.startsWith('template.invoke')) return []
    return props.uiInputFields
})

function isPlainObject(v) {
    return v !== null && typeof v === 'object' && !Array.isArray(v)
}

function deepMerge(target, patch) {
    if (!isPlainObject(target) || !isPlainObject(patch)) return patch
    const out = { ...target }
    for (const k of Object.keys(patch)) {
        const pv = patch[k]
        const tv = out[k]
        out[k] = isPlainObject(tv) && isPlainObject(pv) ? deepMerge(tv, pv) : pv
    }
    return out
}

function getAtPath(obj, path) {
    const keys = Array.isArray(path) ? path : String(path).split('.').filter(Boolean)
    let cur = obj
    for (const k of keys) {
        if (cur == null) return undefined
        cur = cur[k]
    }
    return cur
}

function setAtPath(obj, path, value) {
    const keys = Array.isArray(path) ? path : String(path).split('.').filter(Boolean)
    if (keys.length === 0) return value
    const out = isPlainObject(obj) ? { ...obj } : {}
    let cur = out
    for (let i = 0; i < keys.length - 1; i++) {
        const k = keys[i]
        const next = cur[k]
        cur[k] = isPlainObject(next) ? { ...next } : {}
        cur = cur[k]
    }
    cur[keys[keys.length - 1]] = value
    return out
}

function pickInversePatch(prevData, patch) {
    if (!isPlainObject(patch)) return patch
    const inv = {}
    for (const k of Object.keys(patch)) {
        const pv = patch[k]
        const dv = prevData ? prevData[k] : undefined
        inv[k] = isPlainObject(pv) && isPlainObject(dv) ? pickInversePatch(dv, pv) : dv
    }
    return inv
}

function applyNodeDataPatch(node, dataPatch, mode = 'shallow') {
    if (!node?.data) return node
    if (mode === 'deep') return { ...node, data: deepMerge(node.data, dataPatch) }
    return { ...node, data: { ...node.data, ...dataPatch } }
}

function findNode(elements, nodeId) {
    return elements.find(el => el?.id === nodeId && el?.data) || null
}

function applyCommand(elements, cmd) {
    if (cmd.type === 'CANVAS_SET_ELEMENTS') return cmd.next

    if (cmd.type === 'NODE_PATCH_DATA') {
        const nodeId = cmd.nodeId
        if (!nodeId) return elements
        return elements.map(el => (el?.id === nodeId && el?.data ? applyNodeDataPatch(el, cmd.patch, cmd.mode) : el))
    }

    if (cmd.type === 'NODE_SET_PARAM_AT') {
        const nodeId = cmd.nodeId
        if (!nodeId) return elements
        return elements.map(el => {
            if (el?.id !== nodeId || !el?.data) return el
            const curParams = el.data.params || {}
            const nextParams = setAtPath(curParams, cmd.path, cmd.value)
            return { ...el, data: { ...el.data, params: nextParams } }
        })
    }

    return elements
}

function execute(elements, cmd) {
    if (cmd.type === 'CANVAS_SET_ELEMENTS') {
        return {
            next: cmd.next,
            inverse: { type: 'CANVAS_SET_ELEMENTS', next: elements, groupKey: cmd.groupKey || 'CANVAS_SET_ELEMENTS' }
        }
    }

    if (cmd.type === 'NODE_PATCH_DATA') {
        const nodeId = cmd.nodeId
        const node = nodeId ? findNode(elements, nodeId) : null
        const prevData = node?.data || null
        const inversePatch = pickInversePatch(prevData, cmd.patch)
        return {
            next: applyCommand(elements, cmd),
            inverse: {
                type: 'NODE_PATCH_DATA',
                nodeId,
                patch: inversePatch,
                mode: cmd.mode,
                groupKey: cmd.groupKey || 'NODE_PATCH_DATA'
            }
        }
    }

    if (cmd.type === 'NODE_SET_PARAM_AT') {
        const nodeId = cmd.nodeId
        const node = nodeId ? findNode(elements, nodeId) : null
        const prevParams = node?.data?.params || {}
        const prevValue = getAtPath(prevParams, cmd.path)
        return {
            next: applyCommand(elements, cmd),
            inverse: {
                type: 'NODE_SET_PARAM_AT',
                nodeId,
                path: cmd.path,
                value: prevValue,
                groupKey: cmd.groupKey || 'NODE_SET_PARAM_AT'
            }
        }
    }

    return { next: elements, inverse: null }
}

const undoStack = ref([])
const redoStack = ref([])
const lastGroup = ref({ key: '', ts: 0 })

function setHistorySignals() {
    emit('history:can-undo', undoStack.value.length > 0)
    emit('history:can-redo', redoStack.value.length > 0)
}

function pushUndo(inverseCmd, groupKey) {
    if (!props.enableHistory || !inverseCmd) return
    const now = Date.now()
    const canGroup = groupKey && lastGroup.value.key === groupKey && now - lastGroup.value.ts < props.groupMs

    if (canGroup) {
        undoStack.value = [...undoStack.value.slice(0, -1), inverseCmd].slice(-props.historyLimit)
    } else {
        undoStack.value = [...undoStack.value, inverseCmd].slice(-props.historyLimit)
    }

    lastGroup.value.key = groupKey || ''
    lastGroup.value.ts = now
    redoStack.value = []
    setHistorySignals()
}

function undo() {
    if (!props.enableHistory) return
    const inv = undoStack.value[undoStack.value.length - 1]
    if (!inv) return
    undoStack.value = undoStack.value.slice(0, -1)

    const { next, inverse } = execute(props.elements, inv)
    if (next !== props.elements) {
        if (inverse) redoStack.value = [inverse, ...redoStack.value].slice(0, props.historyLimit)
        emit('update:elements', next)
        emit('history:undo')
    }

    setHistorySignals()
}

function redo() {
    if (!props.enableHistory) return
    const cmd = redoStack.value[0]
    if (!cmd) return
    redoStack.value = redoStack.value.slice(1)

    const { next, inverse } = execute(props.elements, cmd)
    if (next !== props.elements) {
        if (inverse) undoStack.value = [...undoStack.value, inverse].slice(-props.historyLimit)
        emit('update:elements', next)
        emit('history:redo')
    }

    setHistorySignals()
}

let timer = null
let pending = null
let pendingInv = null
let pendingGroup = ''

function dispatch(rawCmd) {
    const cmd = { ...rawCmd }

    if (cmd.type !== 'CANVAS_SET_ELEMENTS') {
        if (!canEdit.value) return
        const nodeId = selectedNodeId.value
        if (!nodeId) return
        cmd.nodeId = cmd.nodeId || nodeId
    }

    const groupKey = cmd.groupKey || cmd.type
    const debounced = !!cmd.debounce

    const { next, inverse } = execute(props.elements, cmd)
    if (next === props.elements) return

    if (!debounced) {
        pushUndo(inverse, groupKey)
        emit('update:elements', next)
        return
    }

    pending = next
    pendingInv = inverse
    pendingGroup = groupKey || pendingGroup

    if (timer) return
    timer = window.setTimeout(() => {
        timer = null
        if (pending) {
            pushUndo(pendingInv, pendingGroup)
            emit('update:elements', pending)
            pending = null
            pendingInv = null
            pendingGroup = ''
        }
    }, props.debounceMs)
}

function updateNodeData(patch) {
    if (!patch || typeof patch !== 'object') return
    dispatch({ type: 'NODE_PATCH_DATA', patch, mode: 'deep', debounce: true, groupKey: 'node.settings' })
}

function updateParams(params) {
    dispatch({ type: 'NODE_PATCH_DATA', patch: { params }, mode: 'shallow', debounce: true, groupKey: 'node.params' })
}

function updateDescription(description) {
    dispatch({ type: 'NODE_PATCH_DATA', patch: { description }, mode: 'shallow', debounce: true, groupKey: 'node.description' })
}

function updateConnections(connections) {
    dispatch({ type: 'NODE_PATCH_DATA', patch: { connections }, mode: 'shallow', debounce: false, groupKey: 'node.connections' })
}

function updateParamAt(path, value) {
    dispatch({ type: 'NODE_SET_PARAM_AT', path, value, debounce: true, groupKey: `node.param.${String(path)}` })
}

function onKeydown(e) {
    if (!props.enableHotkeys) return
    const platform = navigator.userAgentData?.platform || navigator.userAgent || ''
    const isMac = /mac/i.test(String(platform))
    const mod = isMac ? e.metaKey : e.ctrlKey
    if (!mod) return
    const key = String(e.key || '').toLowerCase()
    if (key === 'z' && !e.shiftKey) {
        e.preventDefault()
        undo()
    } else if ((key === 'z' && e.shiftKey) || key === 'y') {
        e.preventDefault()
        redo()
    }
}

onMounted(() => {
    if (props.enableHotkeys) window.addEventListener('keydown', onKeydown, { passive: false })
    setHistorySignals()
})

onBeforeUnmount(() => {
    if (props.enableHotkeys) window.removeEventListener('keydown', onKeydown)
    if (timer) window.clearTimeout(timer)
})

// Expose autoLayout from WorkflowCanvas
function autoLayout() {
    workflowCanvasRef.value?.autoLayout?.()
}

defineExpose({ undo, redo, dispatch, updateParamAt, autoLayout })
</script>

<style scoped>
.workflow-tab-container { display:flex; flex:1; overflow:hidden; }
.workflow-canvas-wrapper { flex:1; display:flex; flex-direction:column; overflow:hidden; }
.node-properties-panel { position:relative; width:380px; background:linear-gradient(180deg,#1e293b 0%,#0f172a 100%); border-left:1px solid #334155; display:flex; flex-direction:column; transition:width .3s ease, min-width .3s ease; }
.node-properties-panel.collapsed { width:0; min-width:0; border-left:none; }
.panel-content { flex:1; display:flex; flex-direction:column; overflow:hidden; transition:opacity .2s; }
.panel-content.hidden { opacity:0; pointer-events:none; }
.panel-body { flex:1; padding:20px; overflow-y:auto; }
.prop-group { margin-bottom:20px; }
.prop-label { display:flex; align-items:center; gap:6px; font-size:12px; font-weight:600; color:#94a3b8; margin-bottom:8px; }
.custom-scrollbar::-webkit-scrollbar { width:6px; }
.custom-scrollbar::-webkit-scrollbar-track { background:transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background:#475569; border-radius:3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background:#64748b; }
.read-only-banner { display:flex; align-items:center; gap:8px; padding:10px 14px; margin-bottom:16px; background:rgba(251,191,36,.1); border:1px solid rgba(251,191,36,.3); border-radius:8px; color:#fbbf24; font-size:12px; font-weight:500; }
.panel-divider { height:1px; background:rgba(51,65,85,0.5); margin:16px 0; }
.panel-actions { display:flex; gap:8px; margin-bottom:16px; }
.panel-actions .ai-suggest-btn,
.panel-actions .preview-results-btn { flex:1; width:auto; margin-bottom:0; }
.ai-suggest-btn { display:flex; align-items:center; gap:6px; padding:8px 12px; margin-bottom:16px; background:rgba(139,92,246,.1); border:1px solid rgba(139,92,246,.3); border-radius:8px; color:#a78bfa; font-size:12px; font-weight:500; cursor:pointer; transition:all .2s ease; width:100%; justify-content:center; }
.ai-suggest-btn:hover { background:rgba(139,92,246,.2); border-color:rgba(139,92,246,.5); color:#c4b5fd; }
.preview-results-btn { display:flex; align-items:center; gap:6px; padding:8px 12px; margin-bottom:16px; background:rgba(34,197,94,.1); border:1px solid rgba(34,197,94,.3); border-radius:8px; color:#4ade80; font-size:12px; font-weight:500; cursor:pointer; transition:all .2s ease; width:100%; justify-content:center; }
.preview-results-btn:hover { background:rgba(34,197,94,.2); border-color:rgba(34,197,94,.5); color:#86efac; }
.panel-sticky-footer { flex-shrink:0; padding:12px 20px; border-top:1px solid rgba(51,65,85,0.5); background:linear-gradient(0deg,#0f172a 0%,rgba(15,23,42,0.95) 60%,transparent 100%); }
.panel-sticky-footer :deep(.delete-section) { margin-top:0; padding-top:0; border-top:none; }
</style>
