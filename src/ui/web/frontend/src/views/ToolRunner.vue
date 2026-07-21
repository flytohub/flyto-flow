<template>
  <div class="tool-runner-page">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <Loader :size="48" class="spin" />
      <span>{{ $t('common.loading') }}</span>
    </div>

    <!-- Error State -->
    <div v-else-if="loadError" class="error-state">
      <AlertCircle :size="48" />
      <h2>{{ $t('toolRunner.toolNotFound') }}</h2>
      <p>{{ loadError }}</p>
      <button class="btn btn-primary" @click="goBack">
        <ArrowLeft :size="16" />
        {{ $t('toolRunner.backToLibrary') }}
      </button>
    </div>

    <!-- Tool Runner -->
    <div v-else-if="tool" class="runner-container">
      <!-- Navigation Bar -->
      <ToolRunnerNavBar
        v-model="viewMode"
        @back="goBack"
        @edit="editTool"
      />

      <!-- Simple Mode: Visual Input -> Output Flow -->
      <SimpleToolView
        v-if="viewMode === 'simple'"
        :tool="tool"
        :show-advanced-toggle="false"
        :show-flow-details="true"
        @toggle-advanced="viewMode = 'advanced'"
      />

      <!-- Advanced Mode: Form + Debug Panels -->
      <div v-else class="advanced-view">
        <div class="advanced-layout">
          <!-- Left: Input Form -->
          <div class="form-panel">
            <div class="panel-header">
              <FormInput :size="18" />
              <span>{{ $t('toolRunner.inputForm') }}</span>
            </div>

            <div class="form-content">
              <SchemaParamsRenderer
                :schema="paramsSchema"
                v-model="inputValues"
                visibility-mode="advanced"
                :allow-expert-toggle="false"
              />

              <!-- Run Button -->
              <button
                class="run-btn"
                :disabled="!canRun || isExecuting"
                @click="executeTool"
              >
                <Loader v-if="isExecuting" :size="20" class="spin" />
                <Play v-else :size="20" />
                {{ isExecuting ? $t('toolRunner.running') : $t('toolRunner.runTool') }}
              </button>
            </div>
          </div>

          <!-- Center: Flow + Resolved Params + Logs -->
          <div class="center-panels">
            <ToolRunnerFlowPanel
              :steps="tool.flow?.steps || []"
              :current-step-index="currentStepIndex"
            />

            <ToolRunnerResolvedPanel
              :steps="tool.flow?.steps || []"
              :input-values="inputValues"
            />

            <ToolRunnerLogsPanel
              :logs="executionLogs"
              :execution-time="executionTime"
            />
          </div>

          <!-- Right: Results -->
          <ToolRunnerResultsPanel
            :result="executionResult"
            :error="executionError"
            @retry="executeTool"
            @download="downloadResult"
            @copy="copyResult"
            @reset="resetExecution"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { get } from '@/api/client'
import { DEFAULTS } from '@/config/defaults'
import { useToolStorage } from '@/composables/useToolStorage'
import { SimpleToolView } from '@/components/tools'
import SchemaParamsRenderer from '@/components/templateBuilder/SchemaParamsRenderer.vue'
import {
  ToolRunnerNavBar,
  ToolRunnerFlowPanel,
  ToolRunnerLogsPanel,
  ToolRunnerResultsPanel,
  ToolRunnerResolvedPanel
} from '@/components/toolRunner'
import { Loader, AlertCircle, ArrowLeft, FormInput, Play } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { loadTool: loadLocalTool, getParamsSchema } = useToolStorage()

// Data source: 'local' (tools from localStorage) or 'server' (templates from API)
const isServerSource = computed(() => route.meta.source === 'server')

// State
const tool = ref(null)
const isLoading = ref(true)
const loadError = ref(null)
const viewMode = ref('simple')
const inputValues = reactive({})
const fileRefs = reactive({})
const isExecuting = ref(false)
const currentStepIndex = ref(-1)
const executionResult = ref(null)
const executionError = ref(null)
const executionTime = ref(null)
const executionLogs = ref([])

// Computed: Convert tool.inputs to params_schema format
const paramsSchema = computed(() => {
  return getParamsSchema(tool.value)
})

// Computed — extract flat field definitions, handling normalized schema format
const inputFields = computed(() => {
  const raw = tool.value?.inputs || tool.value?.meta?.paramsSchema || {}
  const fields = (raw.type === 'object' && raw.properties) ? raw.properties : raw
  if (!fields || typeof fields !== 'object') return []
  return Object.entries(fields)
    .filter(([key]) => key !== 'type' && key !== 'required')
    .map(([key, def]) => ({ key, def: typeof def === 'object' ? def : { type: 'string' } }))
})

const canRun = computed(() => {
  for (const field of inputFields.value) {
    if (field.def.required && !inputValues[field.key]) {
      return false
    }
  }
  return true
})

// Methods
async function loadToolData() {
  isLoading.value = true
  loadError.value = null

  try {
    const toolId = route.params.id
    let loaded = null

    if (isServerSource.value) {
      // Load template from server API
      const data = await get(`/templates/${toolId}`)
      if (data.ok && data.template) {
        // Convert template format to tool format
        loaded = convertTemplateToTool(data.template)
      }
    } else {
      // Load tool from local storage
      loaded = await loadLocalTool(toolId)
    }

    if (loaded) {
      tool.value = loaded
      // Initialize input values from inputs or paramsSchema
      const raw = loaded.inputs || loaded.meta?.paramsSchema || {}
      // Handle {type:"object", properties:{}} normalized format
      const fields = (raw.type === 'object' && raw.properties) ? raw.properties : raw
      for (const [key, def] of Object.entries(fields)) {
        if (key === 'type' || key === 'required') continue
        const fieldDef = typeof def === 'object' ? def : {}
        inputValues[key] = getDefaultValue(fieldDef.type, fieldDef.default)
      }
    } else {
      loadError.value = t('toolRunner.toolNotFoundError')
    }
  } catch (e) {
    loadError.value = e.message || t('toolRunner.loadFailed')
  } finally {
    isLoading.value = false
  }
}

// Convert server template format to tool format
function convertTemplateToTool(template) {
  const yaml = template.yamlContent || template.content || ''
  const rawSchema = template.paramsSchema || {}

  // Extract flat field definitions from normalized {type:"object", properties:{}} format
  const inputs = (rawSchema.type === 'object' && rawSchema.properties)
    ? rawSchema.properties
    : rawSchema

  return {
    id: template.id || template.templateId,
    meta: {
      name: template.name || template.title || 'Untitled',
      description: template.description || '',
      category: template.category || 'other',
      icon: template.icon || 'Box',
      paramsSchema: rawSchema
    },
    inputs,
    flow: {
      steps: parseYamlSteps(yaml)
    },
    _yaml: yaml,
    _source: 'server'
  }
}

// Parse YAML content to extract steps (simplified)
function parseYamlSteps(yamlContent) {
  if (!yamlContent) return []
  try {
    // We'll parse the YAML lazily when executing
    return [{ id: 'step1', module: 'workflow', label: 'Workflow' }]
  } catch (e) {
    return []
  }
}

function getDefaultValue(type, defaultVal) {
  if (defaultVal !== undefined) return defaultVal
  switch (type) {
    case 'number': return 0
    case 'boolean': return false
    case 'file': return null
    default: return ''
  }
}

function goBack() {
  if (isServerSource.value) {
    router.push('/my-templates')
  } else {
    router.push('/tools')
  }
}

function editTool() {
  if (isServerSource.value) {
    router.push(`/templates/builder/${tool.value.id}`)
  } else {
    router.push(`/templates/builder?tab=moduleLab&tool=${tool.value.id}`)
  }
}

function triggerFileInput(key) {
  fileRefs[key]?.click()
}

function handleFileSelect(key, event) {
  const file = event.target.files?.[0]
  if (file) inputValues[key] = file
}

async function executeTool() {
  if (!canRun.value || isExecuting.value) return

  isExecuting.value = true
  executionResult.value = null
  executionError.value = null
  executionTime.value = null
  executionLogs.value = []
  currentStepIndex.value = 0

  const startTime = Date.now()

  addLog('info', 'System', 'Starting execution...')

  try {
    let yamlContent
    const params = { inputs: { ...inputValues } }

    if (tool.value._source === 'server' && tool.value._yaml) {
      // Use existing YAML from server template
      yamlContent = tool.value._yaml
      addLog('info', 'System', 'Using server template YAML')
    } else {
      // Build workflow from local tool
      const workflow = buildWorkflow()
      const yaml = await import('js-yaml')
      yamlContent = yaml.dump(workflow, { indent: 2 })
      addLog('info', 'System', `Workflow built with ${workflow.steps.length} steps`)
    }

    const { workflowAPI } = await import('@/api/workflows')
    const result = await workflowAPI.run(yamlContent, params)

    if (result.ok) {
      addLog('info', 'System', `Execution started (ID: ${result.executionId})`)
      await pollExecution(result.executionId)
    } else {
      addLog('error', 'System', result.error || result.message || t('toolRunner.executionFailed'))
      executionError.value = result.error || result.message || t('toolRunner.executionFailed')
    }
  } catch (e) {
    addLog('error', 'System', e.message || t('toolRunner.executionFailed'))
    executionError.value = e.message || t('toolRunner.executionFailed')
  } finally {
    isExecuting.value = false
    currentStepIndex.value = -1
    executionTime.value = Date.now() - startTime
    addLog('info', 'System', `Completed in ${executionTime.value}ms`)
  }
}

function buildWorkflow() {
  const steps = (tool.value?.flow?.steps || []).map(step => {
    const params = {}
    for (const [paramName, source] of Object.entries(step.params || {})) {
      if (source.from === 'input' && source.key) {
        params[paramName] = `{{ inputs.${source.key} }}`
      } else if (source.from === 'step' && source.stepId) {
        params[paramName] = `{{ steps.${source.stepId}.output.${source.output || 'result'} }}`
      } else if (source.from === 'fixed') {
        params[paramName] = source.value
      }
    }
    return { id: step.id, module: step.module, params }
  })

  return {
    id: `tool_${tool.value?.id || 'run'}`,
    name: tool.value?.meta?.name || 'Tool Execution',
    version: 1,
    steps
  }
}

async function pollExecution(executionId) {
  const maxAttempts = DEFAULTS.LIMITS.MAX_TOOL_ATTEMPTS
  let attempts = 0
  let lastStepIndex = -1

  while (attempts < maxAttempts) {
    attempts++
    await new Promise(r => setTimeout(r, DEFAULTS.TIMING.POLL_RETRY_DELAY))

    try {
      const data = await get(`/executions/${executionId}`)
      if (!data.ok || !data.execution) continue

      const exec = data.execution

      // Log step changes
      const execCurrentStep = exec.currentStep
      if (execCurrentStep !== undefined && execCurrentStep !== lastStepIndex) {
        const steps = tool.value?.flow?.steps || []
        const stepName = steps[execCurrentStep]?.label || steps[execCurrentStep]?.module || `Step ${execCurrentStep + 1}`

        if (lastStepIndex >= 0) {
          const prevStepName = steps[lastStepIndex]?.label || steps[lastStepIndex]?.module || `Step ${lastStepIndex + 1}`
          addLog('success', prevStepName, 'Completed')
        }

        addLog('info', stepName, 'Running...')
        lastStepIndex = execCurrentStep
        currentStepIndex.value = execCurrentStep
      }

      if (exec.status === 'completed') {
        // Log last step completion
        if (lastStepIndex >= 0) {
          const steps = tool.value?.flow?.steps || []
          const stepName = steps[lastStepIndex]?.label || steps[lastStepIndex]?.module || `Step ${lastStepIndex + 1}`
          addLog('success', stepName, 'Completed')
        }
        addLog('success', 'System', 'Execution completed successfully')
        executionResult.value = exec.outputs || exec.result || { result: 'Completed' }
        return
      } else if (exec.status === 'failed') {
        addLog('error', 'System', exec.error || t('toolRunner.executionFailed'))
        executionError.value = exec.error || t('toolRunner.executionFailed')
        return
      }
    } catch (e) {
    }
  }

  addLog('error', 'System', t('toolRunner.executionTimedOut'))
  executionError.value = t('toolRunner.executionTimedOut')
}

function resetExecution() {
  executionResult.value = null
  executionError.value = null
  executionTime.value = null
  executionLogs.value = []
}

// Add execution log entry
function addLog(type, step, message) {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`

  executionLogs.value.push({
    id: Date.now(),
    type, // 'info' | 'success' | 'error' | 'warning'
    step,
    message,
    time
  })
}

function copyResult() {
  navigator.clipboard.writeText(JSON.stringify(executionResult.value, null, 2))
}

function downloadResult() {
  const result = executionResult.value
  if (!result) return
  const url = result.fileUrl || result.downloadUrl
  if (url) {
    window.open(url, '_blank')
  }
}

// Lifecycle
onMounted(() => {
  loadToolData()
})

watch(() => route.params.id, () => {
  loadToolData()
})
</script>

<style scoped>
.tool-runner-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #f1f5f9;
}

/* Loading & Error States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 100vh;
  padding: 20px;
  text-align: center;
}

.error-state h2 { margin: 0; }
.error-state p { color: #94a3b8; margin: 0; }

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Advanced View Layout */
.advanced-view {
  padding: 24px;
}

.advanced-layout {
  display: grid;
  grid-template-columns: 320px 1fr 380px;
  gap: 20px;
  max-width: 1800px;
  margin: 0 auto;
}

.center-panels {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

@media (max-width: 1400px) {
  .advanced-layout {
    grid-template-columns: 300px 1fr 320px;
  }
}

@media (max-width: 1200px) {
  .advanced-layout {
    grid-template-columns: 1fr 1fr;
  }
  .center-panels {
    grid-column: 1 / -1;
    order: -1;
  }
}

@media (max-width: 768px) {
  .advanced-layout {
    grid-template-columns: 1fr;
  }
}

/* Form Panel */
.form-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 16px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.5);
  border-bottom: 1px solid #334155;
  font-size: 14px;
  font-weight: 600;
}

.form-content {
  padding: 20px;
}

/* Run Button */
.run-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 24px;
}

.run-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}

.run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Buttons */
.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}
</style>
